from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.response import ok
from app.core.security import CurrentUser, create_access_token, user_permission_codes, verify_password
from app.db import get_db
from app.models.identity import Role, User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.rbac import permissions_for_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=None)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).options(selectinload(User.roles).selectinload(Role.permissions)).where(User.username == payload.username))
    if not user or user.status != "ACTIVE" or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    permissions = sorted(user_permission_codes(user))
    token = create_access_token(user, permissions)
    return ok(TokenResponse(access_token=token, expires_in=480 * 60).model_dump(), request)


@router.get("/me")
def me(request: Request, user: CurrentUser):
    return ok({"id": user.id, "tenant_id": user.tenant_id, "username": user.username, "display_name": user.display_name, "department_id": user.department_id, "roles": [role.code for role in user.roles], "permissions": sorted(user_permission_codes(user))}, request)
