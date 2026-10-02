from pydantic import BaseModel


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    username: str
    roles: list[str]
