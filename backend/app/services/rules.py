import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.expense import ExpenseReport
from app.models.identity import User
from app.models.rules import Budget, ExpenseCategory, ExpenseRuleCheck, Invoice, InvoiceCheck, InvoiceMatch
from app.schemas.rules import ApprovalRouteRequest, ExpenseRuleRequest, InvoiceValidationRequest, RuleHit


def validate_invoice(payload: InvoiceValidationRequest):
    results = [
        RuleHit(rule="total_equals_amount_plus_tax", passed=payload.total_amount == payload.amount + payload.tax_amount, message="价税合计应等于金额加税额"),
        RuleHit(rule="tax_rate_allowlist", passed=payload.tax_rate in payload.allowed_tax_rates, message="税率必须在白名单内"),
        RuleHit(rule="non_negative_amounts", passed=all(value >= Decimal("0") for value in (payload.amount, payload.tax_amount, payload.total_amount)), message="金额不可为负数"),
    ]
    return {"passed": all(item.passed for item in results), "results": [item.model_dump() for item in results]}


def evaluate_invoice(db: Session, payload: InvoiceValidationRequest, tenant_id: str) -> dict:
    results = [
        RuleHit(rule="total_equals_amount_plus_tax", passed=payload.total_amount == payload.amount + payload.tax_amount, message="价税合计应等于金额加税额"),
        RuleHit(rule="tax_rate_allowlist", passed=payload.tax_rate in payload.allowed_tax_rates, message="税率必须在白名单内"),
        RuleHit(rule="non_negative_amounts", passed=all(value >= Decimal("0") for value in (payload.amount, payload.tax_amount, payload.total_amount)), message="金额不可为负数"),
    ]
    if payload.invoice_no:
        existing = db.scalar(select(Invoice).where(Invoice.tenant_id == tenant_id, Invoice.invoice_no == payload.invoice_no))
        results.append(RuleHit(rule="duplicate_invoice_number", passed=existing is None, message="未发现重复发票号码" if existing is None else "发票号码已存在，疑似重复发票"))
        amount_ok = payload.total_amount <= Decimal("1000000")
        results.append(RuleHit(rule="invoice_amount_range", passed=amount_ok, message="发票金额在允许范围内" if amount_ok else "发票金额超过确定性校验上限"))
        invoice_date_ok = payload.invoice_date is None or date.today() - timedelta(days=365) <= payload.invoice_date <= date.today()
        results.append(RuleHit(rule="invoice_date_range", passed=invoice_date_ok, message="发票日期正常" if invoice_date_ok else "发票日期超出允许范围"))
        status_ok = payload.invoice_status.upper() in {"VALID", "正常", "VALIDATED"}
        results.append(RuleHit(rule="invoice_status", passed=status_ok, message="发票状态正常" if status_ok else "发票状态异常"))
        invoice = existing or Invoice(tenant_id=tenant_id, invoice_no=payload.invoice_no, amount=payload.amount, tax_amount=payload.tax_amount, total_amount=payload.total_amount, invoice_date=payload.invoice_date, status=payload.invoice_status, report_id=payload.report_id, source_file_id=payload.source_file_id)
        if not existing:
            db.add(invoice)
            db.flush()
        db.execute(delete(InvoiceCheck).where(InvoiceCheck.invoice_id == invoice.id))
        for item in results:
            db.add(InvoiceCheck(tenant_id=tenant_id, invoice_id=invoice.id, rule_code=item.rule, passed=item.passed, message=item.message, details_json=json.dumps({}, ensure_ascii=False)))
        if existing:
            db.add(InvoiceMatch(tenant_id=tenant_id, invoice_id=invoice.id, matched_invoice_id=existing.id))
    return {"passed": all(item.passed for item in results), "results": [item.model_dump() for item in results]}


def _category_rule(db: Session, tenant_id: str, category: str) -> ExpenseCategory | None:
    return db.scalar(select(ExpenseCategory).where(ExpenseCategory.tenant_id == tenant_id, ExpenseCategory.active.is_(True), (ExpenseCategory.code == category) | (ExpenseCategory.name == category)))


def evaluate_expense(db: Session, payload: ExpenseRuleRequest, tenant_id: str) -> dict:
    report = db.scalar(select(ExpenseReport).where(ExpenseReport.id == payload.report_id, ExpenseReport.tenant_id == tenant_id))
    if not report:
        return {"passed": False, "risk_level": "HIGH", "checks": [{"rule": "report_exists", "passed": False, "message": "报销单不存在"}]}
    category = _category_rule(db, tenant_id, report.category)
    checks: list[dict] = []
    single_limit = category.single_limit if category else Decimal("0")
    monthly_limit = category.monthly_limit if category else Decimal("0")
    single_passed = single_limit <= 0 or report.total_amount <= single_limit
    checks.append({"rule": "single_expense_limit", "passed": single_passed, "actual": report.total_amount, "limit": single_limit, "message": "未超过单次限额" if single_passed else f"超过单次限额 {single_limit}"})
    start = report.created_at.date().replace(day=1) if report.created_at else date.today().replace(day=1)
    end = start.replace(day=monthrange(start.year, start.month)[1])
    monthly_used = db.scalar(select(func.coalesce(func.sum(ExpenseReport.total_amount), 0)).where(ExpenseReport.tenant_id == tenant_id, ExpenseReport.applicant_id == report.applicant_id, ExpenseReport.created_at >= datetime.combine(start, datetime.min.time()), ExpenseReport.created_at <= datetime.combine(end, datetime.max.time()), ExpenseReport.status.not_in(["CANCELLED", "REJECTED"]))) or Decimal("0")
    monthly_used = Decimal(str(monthly_used))
    monthly_passed = monthly_limit <= 0 or monthly_used <= monthly_limit
    checks.append({"rule": "monthly_expense_limit", "passed": monthly_passed, "actual": monthly_used, "limit": monthly_limit, "message": "未超过月度额度" if monthly_passed else f"超过月度额度 {monthly_limit}"})
    user = db.scalar(select(User).where(User.id == report.applicant_id))
    budget = db.scalar(select(Budget).where(Budget.tenant_id == tenant_id, Budget.fiscal_year == start.year, Budget.department_id == (user.department_id if user else None), (Budget.category_code == report.category) | (Budget.category_code.is_(None))))
    budget_available = (budget.allocated_amount - budget.used_amount - budget.frozen_amount) if budget else Decimal("0")
    budget_passed = budget is None or report.total_amount <= budget_available
    checks.append({"rule": "department_budget", "passed": budget_passed, "actual": report.total_amount, "limit": budget_available, "message": "部门预算充足" if budget_passed else f"部门预算不足，可用余额 {budget_available}"})
    finance_required = bool(category and category.requires_finance)
    checks.append({"rule": "special_expense_finance_review", "passed": True, "actual": None, "limit": None, "message": "特殊费用需要财务审核" if finance_required else "无需额外财务审核"})
    for item in checks:
        db.add(ExpenseRuleCheck(tenant_id=tenant_id, report_id=report.id, rule_code=item["rule"], passed=item["passed"], actual_value=item["actual"], limit_value=item["limit"], message=item["message"]))
    failed = [item for item in checks if not item["passed"]]
    return {"passed": not failed, "risk_level": "HIGH" if failed else "LOW", "finance_required": finance_required, "checks": [{key: str(value) if isinstance(value, Decimal) else value for key, value in item.items()} for item in checks]}


def resolve_approval_route(db: Session, payload: ApprovalRouteRequest, tenant_id: str, current_user_id: str) -> dict:
    report = db.scalar(select(ExpenseReport).where(ExpenseReport.id == payload.report_id, ExpenseReport.tenant_id == tenant_id))
    if not report:
        return {"can_approve": False, "route": [], "reason": "报销单不存在"}
    if payload.approver_id and payload.approver_id == report.applicant_id:
        return {"can_approve": False, "route": [], "reason": "审批人不能审批自己的报销单"}
    category = _category_rule(db, tenant_id, report.category)
    route = ["DEPARTMENT_MANAGER"]
    if report.total_amount >= Decimal("10000"):
        route.append("FINANCE")
    if report.total_amount >= Decimal("100000"):
        route.append("MANAGER")
    if category and category.requires_finance and "FINANCE" not in route:
        route.append("FINANCE")
    return {"can_approve": current_user_id != report.applicant_id, "route": route, "reason": "需要按金额和费用类别逐级审批"}
