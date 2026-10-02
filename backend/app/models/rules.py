from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "invoice_no", name="uq_invoices_tenant_no"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("expense_reports.id", ondelete="SET NULL"), nullable=True)
    invoice_no: Mapped[str] = mapped_column(String(64), nullable=False)
    invoice_type: Mapped[str] = mapped_column(String(32), nullable=False, default="VAT")
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    seller_tax_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    buyer_tax_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="VALID")
    source_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ocr_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class InvoiceCheck(Base):
    __tablename__ = "invoice_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class InvoiceMatch(Base):
    __tablename__ = "invoice_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    matched_invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False, default="DUPLICATE_NUMBER")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    single_limit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    requires_finance: Mapped[bool] = mapped_column(nullable=False, default=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_expense_categories_tenant_code"),)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (Index("ix_budgets_scope", "tenant_id", "fiscal_year", "department_id", "category_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    department_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    category_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    used_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    frozen_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class BudgetUsage(Base):
    __tablename__ = "budget_usages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    budget_id: Mapped[str] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("expense_reports.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RESERVED")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ExpenseRuleCheck(Base):
    __tablename__ = "expense_rule_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("expense_reports.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    limit_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
