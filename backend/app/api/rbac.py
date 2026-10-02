from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.response import ok
from app.core.security import CurrentUser, DataScopeDependency, hash_password, require_permission, user_permission_codes
from app.db import get_db
from app.models.identity import Department, Permission, Role, User
from app.schemas.rbac import DepartmentCreate, PermissionCreate, RoleCreate, UserCreate, UserUpdate
from app.services.rbac import create_user, replace_role_permissions

router = APIRouter(tags=["rbac"])


def user_dict(user: User) -> dict:
    return {"id": user.id, "tenant_id": user.tenant_id, "username": user.username, "display_name": user.display_name, "department_id": user.department_id, "status": user.status, "roles": [role.code for role in user.roles], "permissions": sorted(user_permission_codes(user))}


@router.get("/users")
def list_users(request: Request, user: CurrentUser, scope: DataScopeDependency, db: Session = Depends(get_db)):
    users = db.scalars(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.tenant_id == user.tenant_id)).unique().all()
    visible = [item for item in users if scope.allows(tenant_id=item.tenant_id, user_id=item.id, department_id=item.department_id)]
    return ok([user_dict(item) for item in visible], request)


@router.post("/users", dependencies=[Depends(require_permission("rbac:user:create"))])
def create_user_api(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = create_user(db, payload)
    db.commit()
    db.refresh(user)
    return ok(user_dict(user), request)


@router.patch("/users/{user_id}", dependencies=[Depends(require_permission("rbac:user:update"))])
def update_user(user_id: str, payload: UserUpdate, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for field in ("display_name", "department_id", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)
    if payload.role_codes is not None:
        user.roles = list(db.scalars(select(Role).where(Role.code.in_(payload.role_codes))).all())
    db.commit()
    db.refresh(user)
    return ok(user_dict(user), request)


@router.get("/roles", dependencies=[Depends(require_permission("rbac:role:read"))])
def list_roles(request: Request, db: Session = Depends(get_db)):
    roles = db.scalars(select(Role).options(selectinload(Role.permissions))).all()
    return ok([{"id": role.id, "name": role.name, "code": role.code, "data_scope": role.data_scope, "description": role.description, "permissions": [item.code for item in role.permissions]} for role in roles], request)


@router.post("/roles", dependencies=[Depends(require_permission("rbac:role:create"))])
def create_role(payload: RoleCreate, request: Request, db: Session = Depends(get_db)):
    if db.scalar(select(Role).where(Role.code == payload.code)):
        raise HTTPException(status_code=409, detail="角色编码已存在")
    role = Role(name=payload.name, code=payload.code, data_scope=payload.data_scope, description=payload.description)
    replace_role_permissions(db, role, payload.permission_codes)
    db.add(role)
    db.commit()
    db.refresh(role)
    return ok({"id": role.id, "code": role.code}, request)


@router.get("/permissions", dependencies=[Depends(require_permission("rbac:permission:read"))])
def list_permissions(request: Request, db: Session = Depends(get_db)):
    permissions = db.scalars(select(Permission).order_by(Permission.code)).all()
    return ok([{"id": item.id, "name": item.name, "code": item.code, "resource": item.resource, "action": item.action, "description": item.description} for item in permissions], request)


@router.post("/permissions", dependencies=[Depends(require_permission("rbac:permission:create"))])
def create_permission(payload: PermissionCreate, request: Request, db: Session = Depends(get_db)):
    if db.scalar(select(Permission).where(Permission.code == payload.code)):
        raise HTTPException(status_code=409, detail="权限编码已存在")
    permission = Permission(**payload.model_dump())
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return ok({"id": permission.id, "code": permission.code}, request)


@router.get("/departments")
def list_departments(request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    departments = db.scalars(select(Department).where(Department.tenant_id == user.tenant_id)).all()
    return ok([{"id": item.id, "tenant_id": item.tenant_id, "name": item.name, "parent_id": item.parent_id} for item in departments], request)


@router.post("/departments", dependencies=[Depends(require_permission("rbac:department:create"))])
def create_department(payload: DepartmentCreate, request: Request, db: Session = Depends(get_db)):
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return ok({"id": department.id, "tenant_id": department.tenant_id, "name": department.name, "parent_id": department.parent_id}, request)
