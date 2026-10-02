"""Create deterministic tax and expense rule tables.

Revision ID: 0005_tax_rules
Revises: 0004_file_ocr_jobs
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_tax_rules"
down_revision = "0004_file_ocr_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("expense_reports.id", ondelete="SET NULL")),
        sa.Column("invoice_no", sa.String(64), nullable=False),
        sa.Column("invoice_type", sa.String(32), nullable=False, server_default="VAT"),
        sa.Column("invoice_date", sa.Date()),
        sa.Column("seller_tax_no", sa.String(64)),
        sa.Column("buyer_tax_no", sa.String(64)),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="VALID"),
        sa.Column("source_file_id", sa.String(36)),
        sa.Column("ocr_confidence", sa.Numeric(5, 4)),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "invoice_no", name="uq_invoices_tenant_no"),
        sa.Index("ix_invoices_tenant_id", "tenant_id"),
    )
    op.create_table(
        "invoice_checks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("message", sa.String(512), nullable=False),
        sa.Column("details_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_invoice_checks_tenant_id", "tenant_id"),
        sa.Index("ix_invoice_checks_invoice_id", "invoice_id"),
    )
    op.create_table(
        "invoice_matches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("matched_invoice_id", sa.String(36), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_type", sa.String(32), nullable=False, server_default="DUPLICATE_NUMBER"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "expense_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("single_limit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("monthly_limit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("requires_finance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_expense_categories_tenant_code"),
    )
    op.create_table(
        "budgets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.String(36)),
        sa.Column("category_code", sa.String(64)),
        sa.Column("allocated_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("used_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("frozen_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Index("ix_budgets_scope", "tenant_id", "fiscal_year", "department_id", "category_code"),
    )
    op.create_table(
        "budget_usages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("budget_id", sa.String(36), sa.ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("expense_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="RESERVED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "expense_rule_checks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("expense_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("actual_value", sa.Numeric(18, 2)),
        sa.Column("limit_value", sa.Numeric(18, 2)),
        sa.Column("message", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_expense_rule_checks_tenant_id", "tenant_id"),
        sa.Index("ix_expense_rule_checks_report_id", "report_id"),
    )


def downgrade() -> None:
    op.drop_table("expense_rule_checks")
    op.drop_table("budget_usages")
    op.drop_table("budgets")
    op.drop_table("expense_categories")
    op.drop_table("invoice_matches")
    op.drop_table("invoice_checks")
    op.drop_table("invoices")
