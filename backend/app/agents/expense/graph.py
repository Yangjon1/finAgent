import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy import select

from app.models.expense import ExpenseReport, StoredFile
from app.models.identity import User
from app.models.rules import ExpenseCategory, Invoice
from app.schemas.rules import ApprovalRouteRequest, ExpenseRuleRequest, InvoiceValidationRequest
from app.services.rules import evaluate_expense, evaluate_invoice, resolve_approval_route


class ExpenseState(TypedDict, total=False):
    run_id: str
    report_id: str
    tenant_id: str
    documents: list[dict]
    claim: dict
    extracted_fields: dict
    invoice_results: list[dict]
    duplicate_results: list[dict]
    policy_hits: list[dict]
    budget_result: dict
    risks: list[dict]
    risk_level: str
    recommendation: str
    confidence: float
    approval_route: list[str]
    human_required: bool
    human_decision: str
    payment_status: str
    audit_status: str
    ended_at: str
    errors: list[dict]


def _json_value(value: Any):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    return value


class ExpenseGraph:
    name = "ExpenseGraph"
    version = "0.1.0"

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.checkpointer = MemorySaver()
        builder = StateGraph(ExpenseState)
        builder.add_node("load_claim", self.load_claim)
        builder.add_node("parse_documents", self.parse_documents)
        builder.add_node("extract_invoice", self.extract_invoice)
        builder.add_node("verify_invoice", self.verify_invoice)
        builder.add_node("check_duplicate", self.check_duplicate)
        builder.add_node("retrieve_policy", self.retrieve_policy)
        builder.add_node("check_budget", self.check_budget)
        builder.add_node("risk_analysis", self.risk_analysis)
        builder.add_node("approval_router", self.approval_router)
        builder.add_node("auto_process", self.auto_process)
        builder.add_node("human_review", self.human_review)
        builder.add_node("payment", self.payment)
        builder.add_node("audit", self.audit)
        builder.add_edge(START, "load_claim")
        builder.add_edge("load_claim", "parse_documents")
        builder.add_edge("parse_documents", "extract_invoice")
        builder.add_edge("extract_invoice", "verify_invoice")
        builder.add_edge("verify_invoice", "check_duplicate")
        builder.add_edge("check_duplicate", "retrieve_policy")
        builder.add_edge("retrieve_policy", "check_budget")
        builder.add_edge("check_budget", "risk_analysis")
        builder.add_edge("risk_analysis", "approval_router")
        builder.add_conditional_edges("approval_router", self.route_after_approval, {"auto_process": "auto_process", "human_review": "human_review"})
        builder.add_edge("auto_process", "audit")
        builder.add_conditional_edges("human_review", self.route_after_human, {"payment": "payment", "audit": "audit"})
        builder.add_edge("payment", "audit")
        builder.add_edge("audit", END)
        self.graph = builder.compile(checkpointer=self.checkpointer)

    def invoke(self, state: ExpenseState):
        return self.graph.invoke(state, {"configurable": {"thread_id": state["run_id"]}})

    def resume(self, run_id: str, decision: str):
        return self.graph.invoke(Command(resume=decision), {"configurable": {"thread_id": run_id}})

    def load_claim(self, state: ExpenseState) -> dict:
        db = self.session_factory()
        try:
            report = db.scalar(select(ExpenseReport).where(ExpenseReport.id == state["report_id"], ExpenseReport.tenant_id == state["tenant_id"]))
            if not report:
                return {"errors": [{"node": "load_claim", "message": "报销单不存在"}]}
            user = db.scalar(select(User).where(User.id == report.applicant_id))
            return {"claim": {"id": report.id, "title": report.title, "category": report.category, "total_amount": str(report.total_amount), "applicant_id": report.applicant_id, "department_id": user.department_id if user else None, "status": report.status}}
        finally:
            db.close()

    def parse_documents(self, state: ExpenseState) -> dict:
        db = self.session_factory()
        try:
            files = db.scalars(select(StoredFile).where(StoredFile.tenant_id == state["tenant_id"], StoredFile.owner_type == "expense_report", StoredFile.owner_id == state["report_id"])).all()
            documents = [{"file_id": item.id, "file_name": item.file_name, "ocr_status": item.ocr_status, "ocr_result": json.loads(item.ocr_result_json) if item.ocr_result_json else None} for item in files]
            return {"documents": documents}
        finally:
            db.close()

    def extract_invoice(self, state: ExpenseState) -> dict:
        fields = {}
        for document in state.get("documents", []):
            result = document.get("ocr_result") or {}
            fields.update(result.get("fields") or {})
        return {"extracted_fields": fields}

    def verify_invoice(self, state: ExpenseState) -> dict:
        db = self.session_factory()
        try:
            invoices = db.scalars(select(Invoice).where(Invoice.tenant_id == state["tenant_id"], Invoice.report_id == state["report_id"])).all()
            results = []
            for invoice in invoices:
                result = evaluate_invoice(db, InvoiceValidationRequest(invoice_no=invoice.invoice_no, amount=invoice.amount, tax_amount=invoice.tax_amount, total_amount=invoice.total_amount, invoice_date=invoice.invoice_date, invoice_status=invoice.status), state["tenant_id"])
                results.append(result)
            db.commit()
            return {"invoice_results": results}
        finally:
            db.close()

    def check_duplicate(self, state: ExpenseState) -> dict:
        duplicates = []
        for result in state.get("invoice_results", []):
            duplicates.extend([item for item in result.get("results", []) if item.get("rule") == "duplicate_invoice_number"])
        return {"duplicate_results": duplicates}

    def retrieve_policy(self, state: ExpenseState) -> dict:
        db = self.session_factory()
        try:
            category = db.scalar(select(ExpenseCategory).where(ExpenseCategory.tenant_id == state["tenant_id"], (ExpenseCategory.code == state["claim"]["category"]) | (ExpenseCategory.name == state["claim"]["category"])))
            if not category:
                return {"policy_hits": [], "errors": state.get("errors", []) + [{"node": "retrieve_policy", "message": "未找到费用类别制度配置"}]}
            return {"policy_hits": [{"category": category.code, "single_limit": str(category.single_limit), "monthly_limit": str(category.monthly_limit), "requires_finance": category.requires_finance}]}
        finally:
            db.close()

    def check_budget(self, state: ExpenseState) -> dict:
        db = self.session_factory()
        try:
            result = evaluate_expense(db, ExpenseRuleRequest(report_id=state["report_id"]), state["tenant_id"])
            db.commit()
            return {"budget_result": result}
        finally:
            db.close()

    def risk_analysis(self, state: ExpenseState) -> dict:
        failures = []
        failures.extend([item for result in state.get("invoice_results", []) for item in result.get("results", []) if not item.get("passed")])
        failures.extend([item for item in state.get("budget_result", {}).get("checks", []) if not item.get("passed")])
        failures.extend(state.get("errors", []))
        level = "HIGH" if failures else "LOW"
        return {"risks": failures, "risk_level": level, "confidence": 1.0, "recommendation": "需要人工复核" if failures else "规则校验通过，可进入自动处理分支"}

    def approval_router(self, state: ExpenseState) -> dict:
        db = self.session_factory()
        try:
            result = resolve_approval_route(db, ApprovalRouteRequest(report_id=state["report_id"]), state["tenant_id"], "")
            return {"approval_route": result["route"], "human_required": state.get("risk_level") != "LOW" or bool(state.get("errors"))}
        finally:
            db.close()

    def route_after_approval(self, state: ExpenseState) -> str:
        return "human_review" if state.get("human_required") else "auto_process"

    def auto_process(self, state: ExpenseState) -> dict:
        return {"payment_status": "NOT_STARTED", "recommendation": "低风险规则通过，等待后续付款服务接入"}

    def human_review(self, state: ExpenseState) -> dict:
        decision = interrupt({"type": "human_review", "run_id": state["run_id"], "risk_level": state.get("risk_level"), "risks": state.get("risks", []), "approval_route": state.get("approval_route", [])})
        return {"human_decision": decision}

    def route_after_human(self, state: ExpenseState) -> str:
        return "payment" if state.get("human_decision") == "APPROVE" else "audit"

    def payment(self, state: ExpenseState) -> dict:
        return {"payment_status": "PAYMENT_PENDING", "recommendation": "人工批准，已进入付款待处理状态"}

    def audit(self, state: ExpenseState) -> dict:
        return {"audit_status": "RECORDED", "ended_at": datetime.now(timezone.utc).isoformat()}
