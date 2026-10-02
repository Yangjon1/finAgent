from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.response import ok
from app.core.security import CurrentUser, DataScopeDependency, require_permission
from app.db import get_db
from app.models.expense import ExpenseReport, StoredFile
from app.schemas.expense import AttachmentCreate, ExpenseAction, ExpenseCreate, ExpenseUpdate
from app.services.expense import add_attachment, create_report, get_report, transition, update_report

router = APIRouter(prefix="/expenses", tags=["expenses"])


def report_dict(report: ExpenseReport, files: list[StoredFile] | None = None) -> dict:
    return {"id": report.id, "tenant_id": report.tenant_id, "applicant_id": report.applicant_id, "title": report.title, "category": report.category, "currency": report.currency, "total_amount": str(report.total_amount), "status": report.status, "risk_level": report.risk_level, "current_node": report.current_node, "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None, "version": report.version, "items": [{"id": item.id, "description": item.description, "amount": str(item.amount), "tax_amount": str(item.tax_amount)} for item in report.items], "attachments": [{"id": item.id, "file_name": item.file_name, "object_key": item.object_key, "content_type": item.content_type, "size_bytes": item.size_bytes, "status": item.status} for item in (files or [])]}


def visible_or_404(report: ExpenseReport | None, user: CurrentUser, scope: DataScopeDependency):
    if not report or not scope.allows(tenant_id=report.tenant_id, user_id=report.applicant_id):
        raise HTTPException(status_code=404, detail="报销单不存在")
    return report


@router.get("")
def list_expenses(request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    reports = db.scalars(select(ExpenseReport).options(selectinload(ExpenseReport.items)).where(ExpenseReport.tenant_id == user.tenant_id).order_by(ExpenseReport.created_at.desc())).unique().all()
    visible = [item for item in reports if scope.allows(tenant_id=item.tenant_id, user_id=item.applicant_id)]
    return ok([report_dict(item) for item in visible], request)


@router.post("", dependencies=[Depends(require_permission("expense:create"))])
def create_expense(payload: ExpenseCreate, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    report = create_report(db, payload, user.tenant_id, user.id)
    db.commit()
    report = get_report(db, report.id)
    return ok(report_dict(report), request)


@router.get("/{report_id}")
def get_expense(report_id: str, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    report = visible_or_404(get_report(db, report_id), user, scope)
    files = db.scalars(select(StoredFile).where(StoredFile.owner_type == "expense_report", StoredFile.owner_id == report.id)).all()
    return ok(report_dict(report, files), request)


@router.patch("/{report_id}", dependencies=[Depends(require_permission("expense:update"))])
def update_expense(report_id: str, payload: ExpenseUpdate, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    report = visible_or_404(get_report(db, report_id), user, scope)
    update_report(db, report, payload)
    db.commit()
    return ok(report_dict(get_report(db, report.id)), request)


@router.post("/{report_id}/submit", dependencies=[Depends(require_permission("expense:submit"))])
def submit_expense(report_id: str, payload: ExpenseAction, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    report = visible_or_404(get_report(db, report_id), user, scope)
    transition(report, "SUBMITTED", payload.expected_version)
    db.commit()
    return ok(report_dict(get_report(db, report.id)), request, "报销单已提交")


@router.post("/{report_id}/cancel", dependencies=[Depends(require_permission("expense:update"))])
def cancel_expense(report_id: str, payload: ExpenseAction, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    report = visible_or_404(get_report(db, report_id), user, scope)
    transition(report, "CANCELLED", payload.expected_version)
    db.commit()
    return ok(report_dict(get_report(db, report.id)), request, "报销单已取消")


@router.delete("/{report_id}", dependencies=[Depends(require_permission("expense:delete"))])
def delete_expense(report_id: str, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    report = visible_or_404(get_report(db, report_id), user, scope)
    if report.status != "DRAFT":
        raise HTTPException(status_code=409, detail="只有草稿状态可以删除")
    db.delete(report)
    db.commit()
    return ok({"id": report_id, "deleted": True}, request)


@router.post("/{report_id}/attachments", dependencies=[Depends(require_permission("expense:update"))])
def attach_expense(report_id: str, payload: AttachmentCreate, request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    report = visible_or_404(get_report(db, report_id), user, scope)
    file = add_attachment(db, report, payload)
    db.commit()
    return ok({"id": file.id, "status": file.status, "object_key": file.object_key}, request)
