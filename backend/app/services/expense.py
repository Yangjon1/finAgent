from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import DataScope
from app.models.expense import ExpenseItem, ExpenseReport, StoredFile
from app.schemas.expense import AttachmentCreate, ExpenseCreate, ExpenseUpdate

ALLOWED_TRANSITIONS = {
    "DRAFT": {"SUBMITTED", "CANCELLED"},
    "SUBMITTED": {"APPROVING", "CANCELLED"},
    "APPROVING": {"APPROVED", "REJECTED"},
    "APPROVED": {"PAYING"},
    "PAYING": {"PAID"},
    "PAID": {"ARCHIVED"},
    "REJECTED": {"DRAFT"},
    "CANCELLED": set(),
    "ARCHIVED": set(),
}


def calculate_total(items) -> Decimal:
    return sum((item.amount + item.tax_amount for item in items), Decimal("0"))


def get_report(db: Session, report_id: str) -> ExpenseReport | None:
    return db.scalar(select(ExpenseReport).options(selectinload(ExpenseReport.items)).where(ExpenseReport.id == report_id))


def ensure_visible(report: ExpenseReport, user_id: str, scope: DataScope) -> None:
    if not scope.allows(tenant_id=report.tenant_id, user_id=report.applicant_id):
        raise HTTPException(status_code=404, detail="报销单不存在")


def ensure_version(report: ExpenseReport, expected_version: int) -> None:
    if report.version != expected_version:
        raise HTTPException(status_code=409, detail="报销单版本已变化，请刷新后重试")


def replace_items(report: ExpenseReport, items) -> None:
    report.items = [ExpenseItem(description=item.description, amount=item.amount, tax_amount=item.tax_amount) for item in items]
    report.total_amount = calculate_total(items)


def create_report(db: Session, payload: ExpenseCreate, tenant_id: str, applicant_id: str) -> ExpenseReport:
    report = ExpenseReport(tenant_id=tenant_id, applicant_id=applicant_id, title=payload.title, category=payload.category, currency=payload.currency)
    replace_items(report, payload.items)
    db.add(report)
    db.flush()
    return report


def update_report(db: Session, report: ExpenseReport, payload: ExpenseUpdate) -> ExpenseReport:
    ensure_version(report, payload.expected_version)
    if report.status != "DRAFT":
        raise HTTPException(status_code=409, detail="只有草稿状态可以修改")
    for field in ("title", "category", "currency"):
        value = getattr(payload, field)
        if value is not None:
            setattr(report, field, value)
    if payload.items is not None:
        replace_items(report, payload.items)
    report.version += 1
    db.flush()
    return report


def transition(report: ExpenseReport, target: str, expected_version: int) -> None:
    ensure_version(report, expected_version)
    if target not in ALLOWED_TRANSITIONS.get(report.status, set()):
        raise HTTPException(status_code=409, detail=f"不允许从 {report.status} 转换到 {target}")
    report.status = target
    report.version += 1
    if target == "SUBMITTED":
        report.submitted_at = datetime.now(timezone.utc)


def add_attachment(db: Session, report: ExpenseReport, payload: AttachmentCreate) -> StoredFile:
    if ".." in payload.object_key or payload.object_key.startswith(("/", "\\")):
        raise HTTPException(status_code=422, detail="附件对象路径不合法")
    file = StoredFile(tenant_id=report.tenant_id, owner_type="expense_report", owner_id=report.id, status="PENDING_UPLOAD", **payload.model_dump())
    db.add(file)
    db.flush()
    return file
