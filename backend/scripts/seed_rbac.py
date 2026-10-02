import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db import SessionLocal
from app.models.rules import Budget, ExpenseCategory
from app.models.knowledge import KnowledgeBase
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
    ("文件预签名", "file:presign", "file", "presign"),
    ("文件确认", "file:complete", "file", "complete"),
    ("文件查看", "file:read", "file", "read"),
    ("发票规则校验", "rule:invoice:validate", "rule", "invoice"),
    ("报销规则评估", "rule:expense:evaluate", "rule", "expense"),
    ("审批路由计算", "rule:approval:route", "rule", "approval"),
    ("报销 Agent 运行", "agent:expense:run", "agent", "run"),
    ("报销 Agent 查看", "agent:expense:read", "agent", "read"),
    ("报销 Agent 恢复", "agent:expense:resume", "agent", "resume"),
    ("知识库创建", "knowledge:base:create", "knowledge", "base"),
    ("知识文档索引", "knowledge:document:index", "knowledge", "index"),
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
        for code, name, single_limit, monthly_limit, requires_finance in [
            ("差旅费", "差旅费", "400", "5000", False),
            ("办公费", "办公费", "1000", "5000", False),
            ("招待费", "招待费", "300", "3000", True),
        ]:
            category = db.scalar(select(ExpenseCategory).where(ExpenseCategory.tenant_id == tenant.id, ExpenseCategory.code == code))
            if not category:
                db.add(ExpenseCategory(tenant_id=tenant.id, code=code, name=name, single_limit=single_limit, monthly_limit=monthly_limit, requires_finance=requires_finance))
        db.flush()
        if not db.scalar(select(Budget).where(Budget.tenant_id == tenant.id, Budget.fiscal_year == datetime.now().year, Budget.department_id == department.id)):
            db.add(Budget(tenant_id=tenant.id, fiscal_year=datetime.now().year, department_id=department.id, category_code=None, allocated_amount="100000", used_amount="0", frozen_amount="0", version=1))
        for code, name in [("expense_policy", "报销管理制度"), ("travel_policy", "差旅管理制度"), ("expense_standard", "费用标准"), ("invoice_policy", "发票管理制度"), ("contract_policy", "合同管理制度"), ("procurement_policy", "采购管理制度"), ("approval_policy", "审批制度")]:
            get_or_create(db, KnowledgeBase, tenant_id=tenant.id, code=code, name=name, description=f"{name}知识库", status="ACTIVE")
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
