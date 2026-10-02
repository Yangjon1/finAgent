from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseItemCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=64)
    currency: str = Field(default="CNY", min_length=3, max_length=8)
    items: list[ExpenseItemCreate] = Field(min_length=1)


class ExpenseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    items: list[ExpenseItemCreate] | None = Field(default=None, min_length=1)
    expected_version: int = Field(ge=1)


class ExpenseAction(BaseModel):
    expected_version: int = Field(ge=1)


class AttachmentCreate(BaseModel):
    object_key: str = Field(min_length=1, max_length=512)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(ge=0, le=50 * 1024 * 1024)
