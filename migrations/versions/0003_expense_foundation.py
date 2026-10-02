"""Create the Phase 2 expense foundation.

Revision ID: 0003_expense_foundation
Revises: 0002_rbac
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_expense_foundation"
down_revision = "0002_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expense_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("applicant_id", sa.String(36), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CNY"),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("current_node", sa.String(64)),
        sa.Column("submitted_at", sa.DateTime()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_expense_reports_tenant_id", "tenant_id"),
        sa.Index("ix_expense_reports_applicant_id", "applicant_id"),
        sa.Index("ix_expense_reports_tenant_status", "tenant_id", "status"),
    )
    op.create_table(
        "expense_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("expense_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_expense_items_report_id", "report_id"),
    )
    op.create_table(
        "files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("owner_type", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_UPLOAD"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_files_tenant_id", "tenant_id"),
        sa.Index("ix_files_owner_id", "owner_id"),
    )


def downgrade() -> None:
    op.drop_table("files")
    op.drop_table("expense_items")
    op.drop_table("expense_reports")
