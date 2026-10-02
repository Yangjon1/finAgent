from decimal import Decimal

from app.schemas.rules import InvoiceValidationRequest, InvoiceValidationResponse, RuleHit


def validate_invoice(payload: InvoiceValidationRequest) -> InvoiceValidationResponse:
    results = [
        RuleHit(rule="total_equals_amount_plus_tax", passed=payload.total_amount == payload.amount + payload.tax_amount, message="价税合计应等于金额加税额"),
        RuleHit(rule="tax_rate_allowlist", passed=payload.tax_rate in payload.allowed_tax_rates, message="税率必须在白名单内"),
        RuleHit(rule="non_negative_amounts", passed=all(v >= Decimal("0") for v in (payload.amount, payload.tax_amount, payload.total_amount)), message="金额不可为负数"),
    ]
    return InvoiceValidationResponse(passed=all(item.passed for item in results), results=results)
