"""Create enterprise knowledge base tables.

Revision ID: 0007_knowledge_base
Revises: 0006_agent_runs
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_knowledge_base"
down_revision = "0006_agent_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_knowledge_bases_tenant_code"),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("knowledge_base_id", sa.String(36), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.String(36)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="TEXT"),
        sa.Column("status", sa.String(32), nullable=False, server_default="INDEXING"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(512)),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_knowledge_documents_tenant_kb", "tenant_id", "knowledge_base_id"),
    )
    op.create_table(
        "file_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_no", sa.Integer()),
        sa.Column("vector_id", sa.String(36), nullable=False),
        sa.Column("metadata_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_file_chunks_tenant_document", "tenant_id", "document_id"),
    )


def downgrade() -> None:
    op.drop_table("file_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("knowledge_bases")
