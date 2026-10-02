from decimal import Decimal

from pydantic import BaseModel, Field


class InvoiceValidationRequest(BaseModel):
    amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(ge=0, le=1)
    allowed_tax_rates: list[Decimal] = Field(default_factory=lambda: [Decimal("0"), Decimal("0.01"), Decimal("0.03"), Decimal("0.06"), Decimal("0.09"), Decimal("0.13")])


class RuleHit(BaseModel):
    rule: str
    passed: bool
    message: str


class InvoiceValidationResponse(BaseModel):
    passed: bool
    results: list[RuleHit]
