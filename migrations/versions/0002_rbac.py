"""Add RBAC tables and user password hashes.

Revision ID: 0002_rbac
Revises: 0001_identity_foundation
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_rbac"
down_revision = "0001_identity_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))
    op.drop_column("users", "roles_json")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), existing_nullable=True, nullable=False)
    op.alter_column("users", "updated_at", existing_type=sa.DateTime(), existing_nullable=True, nullable=False, server_default=sa.func.now())

    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36)),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("data_scope", sa.String(32), nullable=False, server_default="TENANT"),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Index("ix_roles_tenant_id", "tenant_id"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(128), nullable=False, unique=True),
        sa.Column("resource", sa.String(64), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.add_column("users", sa.Column("roles_json", sa.Text(), nullable=False, server_default="[]"))
    op.drop_column("users", "updated_at")
    op.drop_column("users", "password_hash")
