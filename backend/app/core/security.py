from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db import get_db
from app.models.identity import Permission, Role, User

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user: User, permissions: list[str], expires_minutes: int = 480) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "roles": [role.code for role in user.roles],
        "permissions": permissions,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或已过期的令牌") from exc


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌缺少用户信息")
    user = db.scalar(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.id == user_id))
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    if payload.get("tenant_id") != user.tenant_id:
        raise HTTPException(status_code=401, detail="令牌租户信息不匹配")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def user_permission_codes(user: User) -> set[str]:
    return {permission.code for role in user.roles for permission in role.permissions}


def require_permission(code: str):
    def dependency(user: CurrentUser) -> User:
        if "*" not in user_permission_codes(user) and code not in user_permission_codes(user):
            raise HTTPException(status_code=403, detail=f"缺少权限: {code}")
        return user

    return dependency


class DataScope:
    def __init__(self, user: User):
        self.tenant_id = user.tenant_id
        self.user_id = user.id
        self.department_id = user.department_id
        self.scopes = {role.data_scope for role in user.roles}

    @property
    def is_all(self) -> bool:
        return "ALL" in self.scopes or "*" in self.scopes

    def allows(self, *, tenant_id: str, user_id: str | None = None, department_id: str | None = None) -> bool:
        if tenant_id != self.tenant_id:
            return False
        if self.is_all or "TENANT" in self.scopes:
            return True
        if "DEPARTMENT" in self.scopes and department_id == self.department_id:
            return True
        return "SELF" in self.scopes and user_id == self.user_id


def get_data_scope(user: CurrentUser) -> DataScope:
    return DataScope(user)


DataScopeDependency = Annotated[DataScope, Depends(get_data_scope)]
