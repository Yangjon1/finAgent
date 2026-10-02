"""Create Agent Run persistence.

Revision ID: 0006_agent_runs
Revises: 0005_tax_rules
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_agent_runs"
down_revision = "0005_tax_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("business_type", sa.String(32), nullable=False),
        sa.Column("business_id", sa.String(36), nullable=False),
        sa.Column("graph_name", sa.String(64), nullable=False),
        sa.Column("graph_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="RUNNING"),
        sa.Column("model_name", sa.String(128)),
        sa.Column("input_hash", sa.String(64)),
        sa.Column("state_json", sa.Text()),
        sa.Column("output_json", sa.Text()),
        sa.Column("error_message", sa.String(512)),
        sa.Column("human_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime()),
        sa.Index("ix_agent_runs_tenant_business", "tenant_id", "business_type", "business_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_runs")
