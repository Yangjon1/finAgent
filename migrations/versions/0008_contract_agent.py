"""Create contract risk and review tables.

Revision ID: 0008_contract_agent
Revises: 0007_knowledge_base
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_contract_agent"
down_revision = "0007_knowledge_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("counterparty_id", sa.String(36)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("contract_no", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("current_version_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_contracts_tenant_status", "tenant_id", "status"),
    )
    op.create_table(
        "contract_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("file_id", sa.String(36)),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="CURRENT"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_contract_versions_contract_id", "contract_id"),
    )
    op.create_table(
        "contract_clauses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("version_id", sa.String(36), sa.ForeignKey("contract_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_no", sa.String(32), nullable=False),
        sa.Column("clause_type", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_no", sa.Integer()),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("found", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "contract_risks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_id", sa.String(36)),
        sa.Column("risk_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_contract_risks_contract_id", "contract_id"),
    )
    op.create_table(
        "contract_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.String(36), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_contract_reviews_contract_id", "contract_id"),
    )


def downgrade() -> None:
    op.drop_table("contract_reviews")
    op.drop_table("contract_risks")
    op.drop_table("contract_clauses")
    op.drop_table("contract_versions")
    op.drop_table("contracts")
