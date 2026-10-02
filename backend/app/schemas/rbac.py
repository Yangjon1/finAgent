from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    tenant_id: str
    department_id: str | None = None
    role_codes: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    department_id: str | None = None
    status: str | None = None
    role_codes: list[str] | None = None


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=2, max_length=64, pattern=r"^[A-Z0-9_]+$")
    data_scope: str = "TENANT"
    description: str = ""
    permission_codes: list[str] = Field(default_factory=list)


class PermissionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9:._-]+$")
    resource: str
    action: str
    description: str = ""


class DepartmentCreate(BaseModel):
    tenant_id: str
    name: str = Field(min_length=1, max_length=128)
    parent_id: str | None = None
