import re
from datetime import datetime, timezone
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy import delete, select

from app.models.contract import Contract, ContractClause, ContractRisk, ContractVersion
from app.services.knowledge import search_knowledge


class ContractState(TypedDict, total=False):
    run_id: str
    contract_id: str
    tenant_id: str
    contract: dict
    document_text: str
    extracted_contract: dict
    clauses: list[dict]
    policy_hits: list[dict]
    rule_results: list[dict]
    risks: list[dict]
    risk_level: str
    approval_route: list[str]
    human_decision: str
    archive_status: str
    errors: list[dict]
    ended_at: str


REQUIRED_CLAUSES = {
    "PAYMENT": ["付款", "支付"],
    "DEFAULT": ["违约", "违约责任"],
    "DISPUTE": ["争议解决", "仲裁", "诉讼"],
    "ACCEPTANCE": ["验收", "交付"],
    "CONFIDENTIALITY": ["保密"],
    "IP": ["知识产权", "著作权"],
}


class ContractGraph:
    name = "ContractGraph"
    version = "0.1.0"

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.checkpointer = MemorySaver()
        builder = StateGraph(ContractState)
        for name in ("load_contract", "parse_document", "extract_contract", "extract_clauses", "retrieve_policy", "rule_check", "risk_analysis", "risk_classification", "approval_router", "human_review", "archive"):
            builder.add_node(name, getattr(self, name))
        builder.add_edge(START, "load_contract")
        builder.add_edge("load_contract", "parse_document")
        builder.add_edge("parse_document", "extract_contract")
        builder.add_edge("extract_contract", "extract_clauses")
        builder.add_edge("extract_clauses", "retrieve_policy")
        builder.add_edge("retrieve_policy", "rule_check")
        builder.add_edge("rule_check", "risk_analysis")
        builder.add_edge("risk_analysis", "risk_classification")
        builder.add_edge("risk_classification", "approval_router")
        builder.add_edge("approval_router", "human_review")
        builder.add_edge("human_review", "archive")
        builder.add_edge("archive", END)
        self.graph = builder.compile(checkpointer=self.checkpointer)

    def invoke(self, state: ContractState):
        return self.graph.invoke(state, {"configurable": {"thread_id": state["run_id"]}})

    def resume(self, run_id: str, decision: str):
        return self.graph.invoke(Command(resume=decision), {"configurable": {"thread_id": run_id}})

    def load_contract(self, state: ContractState) -> dict:
        db = self.session_factory()
        try:
            contract = db.scalar(select(Contract).where(Contract.id == state["contract_id"], Contract.tenant_id == state["tenant_id"]))
            version = db.scalar(select(ContractVersion).where(ContractVersion.contract_id == state["contract_id"]).order_by(ContractVersion.version_no.desc()))
            if not contract or not version:
                return {"errors": [{"node": "load_contract", "message": "合同或合同版本不存在"}]}
            return {"contract": {"id": contract.id, "title": contract.title, "contract_no": contract.contract_no, "owner_id": contract.owner_id, "status": contract.status}, "document_text": version.raw_text}
        finally:
            db.close()

    def parse_document(self, state: ContractState) -> dict:
        text = re.sub(r"\s+", " ", state.get("document_text", "")).strip()
        return {"document_text": text}

    def extract_contract(self, state: ContractState) -> dict:
        text = state.get("document_text", "")
        amount_match = re.search(r"(?:合同金额|总金额|金额)\s*[:：]?\s*([0-9][0-9,]*(?:\.\d+)?)", text)
        advance_match = re.search(r"(?:预付款|预付)\s*(?:比例|款)?\s*[:：]?\s*([0-9]+(?:\.\d+)?)\s*%", text)
        return {"extracted_contract": {"amount": amount_match.group(1).replace(",", "") if amount_match else None, "advance_percent": advance_match.group(1) if advance_match else None}}

    def extract_clauses(self, state: ContractState) -> dict:
        text = state.get("document_text", "")
        clauses = []
        for index, (clause_type, keywords) in enumerate(REQUIRED_CLAUSES.items(), 1):
            evidence = next((keyword for keyword in keywords if keyword in text), None)
            clauses.append({"clause_no": str(index), "clause_type": clause_type, "text": evidence or "", "required": True, "found": evidence is not None})
        db = self.session_factory()
        try:
            version = db.scalar(select(ContractVersion).where(ContractVersion.contract_id == state["contract_id"]).order_by(ContractVersion.version_no.desc()))
            if version:
                db.query(ContractClause).filter(ContractClause.version_id == version.id).delete()
                for clause in clauses:
                    db.add(ContractClause(tenant_id=state["tenant_id"], version_id=version.id, clause_no=clause["clause_no"], clause_type=clause["clause_type"], text=clause["text"], required=clause["required"], found=clause["found"]))
                db.commit()
        finally:
            db.close()
        return {"clauses": clauses}

    def retrieve_policy(self, state: ContractState) -> dict:
        hits = search_knowledge(state["tenant_id"], "合同管理制度 合同审核 必备条款 付款 违约 争议解决", top_k=5)
        return {"policy_hits": hits}

    def rule_check(self, state: ContractState) -> dict:
        results = []
        for clause in state.get("clauses", []):
            if clause["required"] and not clause["found"]:
                results.append({"rule": f"required_clause:{clause['clause_type']}", "passed": False, "message": f"缺少必备条款：{clause['clause_type']}"})
        advance = state.get("extracted_contract", {}).get("advance_percent")
        if advance and float(advance) > 50:
            results.append({"rule": "advance_payment_ratio", "passed": False, "message": "预付款比例超过50%"})
        return {"rule_results": results}

    def risk_analysis(self, state: ContractState) -> dict:
        risks = [{"risk_type": item["rule"], "severity": "HIGH", "description": item["message"], "evidence": item["message"], "recommendation": "补充或修改合同条款"} for item in state.get("rule_results", []) if not item["passed"]]
        return {"risks": risks}

    def risk_classification(self, state: ContractState) -> dict:
        count = len(state.get("risks", []))
        return {"risk_level": "HIGH" if count >= 2 else "MEDIUM" if count == 1 else "LOW"}

    def approval_router(self, state: ContractState) -> dict:
        route = ["BUSINESS_OWNER"]
        if state.get("risk_level") in {"MEDIUM", "HIGH"}:
            route.append("LEGAL")
        if state.get("risk_level") == "HIGH":
            route.extend(["FINANCE", "MANAGER"])
        return {"approval_route": route}

    def human_review(self, state: ContractState) -> dict:
        decision = interrupt({"type": "contract_human_review", "run_id": state["run_id"], "risk_level": state.get("risk_level"), "risks": state.get("risks", []), "approval_route": state.get("approval_route", [])})
        return {"human_decision": decision}

    def archive(self, state: ContractState) -> dict:
        db = self.session_factory()
        try:
            contract = db.scalar(select(Contract).where(Contract.id == state["contract_id"], Contract.tenant_id == state["tenant_id"]))
            if contract:
                contract.risk_level = state.get("risk_level", "UNKNOWN")
                contract.status = "ARCHIVED" if state.get("human_decision") == "APPROVE" else "REJECTED"
                for risk in state.get("risks", []):
                    db.add(ContractRisk(tenant_id=state["tenant_id"], contract_id=contract.id, risk_type=risk["risk_type"], severity=risk["severity"], description=risk["description"], evidence=risk["evidence"], recommendation=risk["recommendation"], status="OPEN"))
                db.commit()
            return {"archive_status": "ARCHIVED" if state.get("human_decision") == "APPROVE" else "REJECTED", "ended_at": datetime.now(timezone.utc).isoformat()}
        finally:
            db.close()
