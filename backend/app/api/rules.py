from fastapi import APIRouter, Request

from app.core.response import ok
from app.schemas.rules import InvoiceValidationRequest
from app.services.rules import validate_invoice

router = APIRouter(prefix="/invoices", tags=["rules"])


@router.post("/validate")
def validate(payload: InvoiceValidationRequest, request: Request):
    return ok(validate_invoice(payload).model_dump(mode="json"), request)
