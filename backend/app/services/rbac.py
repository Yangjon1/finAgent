from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.identity import Permission, Role, User
from app.schemas.rbac import RoleCreate, UserCreate
from app.core.security import hash_password


def permissions_for_user(db: Session, user: User) -> list[str]:
    roles = db.scalars(select(Role).options(selectinload(Role.permissions)).join(User.roles).where(User.id == user.id)).unique().all()
    return sorted({permission.code for role in roles for permission in role.permissions})


def create_user(db: Session, payload: UserCreate) -> User:
    roles = db.scalars(select(Role).where(Role.code.in_(payload.role_codes))).all() if payload.role_codes else []
    user = User(
        tenant_id=payload.tenant_id,
        username=payload.username,
        display_name=payload.display_name,
        department_id=payload.department_id,
        password_hash=hash_password(payload.password),
        roles=roles,
    )
    db.add(user)
    db.flush()
    return user


def replace_role_permissions(db: Session, role: Role, codes: list[str]) -> None:
    role.permissions = list(db.scalars(select(Permission).where(Permission.code.in_(codes))).all())
