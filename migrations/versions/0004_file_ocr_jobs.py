"""Add file upload metadata and OCR jobs.

Revision ID: 0004_file_ocr_jobs
Revises: 0003_expense_foundation
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_file_ocr_jobs"
down_revision = "0003_expense_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("files", sa.Column("sha256", sa.String(64), nullable=True))
    op.add_column("files", sa.Column("ocr_status", sa.String(32), nullable=False, server_default="NOT_STARTED"))
    op.add_column("files", sa.Column("ocr_result_json", sa.Text(), nullable=True))
    op.add_column("files", sa.Column("error_message", sa.String(512), nullable=True))
    op.add_column("files", sa.Column("uploaded_at", sa.DateTime(), nullable=True))
    op.create_table(
        "job_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="QUEUED"),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Index("ix_job_records_tenant_id", "tenant_id"),
        sa.Index("ix_job_records_resource_id", "resource_id"),
    )


def downgrade() -> None:
    op.drop_table("job_records")
    op.drop_column("files", "uploaded_at")
    op.drop_column("files", "error_message")
    op.drop_column("files", "ocr_result_json")
    op.drop_column("files", "ocr_status")
    op.drop_column("files", "sha256")
