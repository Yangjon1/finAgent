from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.security import CurrentUser, require_permission
from app.db import get_db
from app.schemas.rules import ApprovalRouteRequest, ExpenseRuleRequest, InvoiceValidationRequest
from app.services.rules import evaluate_expense, evaluate_invoice, resolve_approval_route

router = APIRouter(prefix="/invoices", tags=["rules"])


@router.post("/validate", dependencies=[Depends(require_permission("rule:invoice:validate"))])
def validate(payload: InvoiceValidationRequest, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    result = evaluate_invoice(db, payload, user.tenant_id)
    db.commit()
    return ok(result, request)


rules_router = APIRouter(prefix="/rules", tags=["rules"])


@rules_router.post("/expenses/evaluate", dependencies=[Depends(require_permission("rule:expense:evaluate"))])
def evaluate(payload: ExpenseRuleRequest, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    result = evaluate_expense(db, payload, user.tenant_id)
    db.commit()
    return ok(result, request)


@rules_router.post("/approval-route", dependencies=[Depends(require_permission("rule:approval:route"))])
def approval_route(payload: ApprovalRouteRequest, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    return ok(resolve_approval_route(db, payload, user.tenant_id, user.id), request)
