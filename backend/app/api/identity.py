from fastapi import APIRouter, Request

from app.core.response import ok
from app.core.security import CurrentUser, user_permission_codes

router = APIRouter(tags=["identity"])


@router.get("/me")
def me(request: Request, user: CurrentUser):
    return ok({"user_id": user.id, "tenant_id": user.tenant_id, "username": user.username, "roles": [role.code for role in user.roles], "permissions": sorted(user_permission_codes(user))}, request)
