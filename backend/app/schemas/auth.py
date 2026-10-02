from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserView(BaseModel):
    id: str
    tenant_id: str
    username: str
    display_name: str
    department_id: str | None
    roles: list[str]
    permissions: list[str]
