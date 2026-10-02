from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.core.security import DataScope
from app.db import Base, get_db
from app.main import app
from app.models.identity import Permission, Role, Tenant, User


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    tenant = Tenant(id="tenant-1", name="测试租户")
    permission_codes = [("permission-1", "rbac:role:create", "role", "create"), ("permission-2", "expense:create", "expense", "create"), ("permission-3", "expense:update", "expense", "update"), ("permission-4", "expense:submit", "expense", "submit"), ("permission-5", "expense:delete", "expense", "delete"), ("permission-6", "expense:read", "expense", "read")]
    permissions = [Permission(id=item[0], name=item[1], code=item[1], resource=item[2], action=item[3]) for item in permission_codes]
    role = Role(id="role-1", tenant_id=tenant.id, name="管理员", code="ADMIN", data_scope="ALL", permissions=permissions)
    user = User(id="user-1", tenant_id=tenant.id, username="admin", display_name="管理员", password_hash=hash_password("Admin@123456"), roles=[role])
    db.add_all([tenant, *permissions, role, user])
    db.commit()
    db.close()

    def override_db():
        session: Session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def login(client: TestClient) -> str:
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123456"})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_login_and_current_user(client: TestClient):
    token = login(client)
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "admin"
    assert "rbac:role:create" in response.json()["data"]["permissions"]


def test_permission_dependency_allows_authorized_user(client: TestClient):
    token = login(client)
    response = client.post("/api/v1/roles", headers={"Authorization": f"Bearer {token}"}, json={"name": "新角色", "code": "NEW_ROLE"})
    assert response.status_code == 200


def test_permission_dependency_rejects_missing_permission(client: TestClient):
    token = login(client)
    response = client.post("/api/v1/permissions", headers={"Authorization": f"Bearer {token}"}, json={"name": "新权限", "code": "demo:read", "resource": "demo", "action": "read"})
    assert response.status_code == 403


def test_authentication_is_required(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_data_scope_is_tenant_safe():
    class RoleStub:
        data_scope = "DEPARTMENT"

    class UserStub:
        tenant_id = "tenant-1"
        id = "user-1"
        department_id = "dept-1"
        roles = [RoleStub()]

    scope = DataScope(UserStub())
    assert scope.allows(tenant_id="tenant-1", department_id="dept-1")
    assert not scope.allows(tenant_id="tenant-2", department_id="dept-1")
    assert not scope.allows(tenant_id="tenant-1", department_id="dept-2")
