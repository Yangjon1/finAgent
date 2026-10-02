import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db import SessionLocal
from app.models.identity import Department, Permission, Role, Tenant, User


PERMISSIONS = [
    ("用户查看", "rbac:user:read", "user", "read"),
    ("用户创建", "rbac:user:create", "user", "create"),
    ("用户修改", "rbac:user:update", "user", "update"),
    ("角色查看", "rbac:role:read", "role", "read"),
    ("角色创建", "rbac:role:create", "role", "create"),
    ("权限查看", "rbac:permission:read", "permission", "read"),
    ("权限创建", "rbac:permission:create", "permission", "create"),
    ("部门创建", "rbac:department:create", "department", "create"),
    ("报销查看", "expense:read", "expense", "read"),
    ("报销创建", "expense:create", "expense", "create"),
    ("报销修改", "expense:update", "expense", "update"),
    ("报销提交", "expense:submit", "expense", "submit"),
    ("报销删除", "expense:delete", "expense", "delete"),
]


def get_or_create(db, model, **values):
    key = values.get("code") or values.get("username") or values.get("name")
    field = model.code if "code" in values and hasattr(model, "code") else model.username if hasattr(model, "username") and "username" in values else model.name
    item = db.scalar(select(model).where(field == key))
    if item:
        return item
    item = model(**values)
    db.add(item)
    db.flush()
    return item


def main() -> None:
    db = SessionLocal()
    try:
        tenant = get_or_create(db, Tenant, id="demo-tenant", name="演示租户", status="ACTIVE")
        department = get_or_create(db, Department, id="demo-dept", tenant_id=tenant.id, name="总部", parent_id=None)
        permission_items = []
        for name, code, resource, action in PERMISSIONS:
            permission_items.append(get_or_create(db, Permission, name=name, code=code, resource=resource, action=action, description=""))

        admin = get_or_create(db, Role, name="系统管理员", code="ADMIN", data_scope="ALL", description="全局管理权限")
        admin.permissions = permission_items
        for name, code in [("普通员工", "EMPLOYEE"), ("部门负责人", "DEPARTMENT_MANAGER"), ("财务人员", "FINANCE"), ("法务人员", "LEGAL"), ("管理人员", "MANAGER")]:
            get_or_create(db, Role, name=name, code=code, tenant_id=tenant.id, data_scope="TENANT", description="")
        username = os.getenv("SEED_ADMIN_USERNAME", "admin")
        password = os.getenv("SEED_ADMIN_PASSWORD", "Admin@123456")
        user = get_or_create(db, User, tenant_id=tenant.id, username=username, display_name="系统管理员", department_id=department.id, password_hash=hash_password(password), status="ACTIVE")
        user.roles = [admin]
        db.commit()
        print(f"RBAC seed complete: username={username}, tenant={tenant.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
