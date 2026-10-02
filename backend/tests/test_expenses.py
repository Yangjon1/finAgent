from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db import Base, get_db
from app.main import app
from app.models.identity import Permission, Role, Tenant, User


@pytest.fixture()
def expense_client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    tenant = Tenant(id="tenant-expense", name="报销租户")
    codes = ["expense:create", "expense:update", "expense:submit", "expense:delete", "expense:read"]
    permissions = [Permission(id=f"p-{index}", name=code, code=code, resource="expense", action=code.split(":")[-1]) for index, code in enumerate(codes)]
    role = Role(id="role-expense", tenant_id=tenant.id, name="员工", code="EXPENSE_USER", data_scope="SELF", permissions=permissions)
    user = User(id="user-expense", tenant_id=tenant.id, username="expense-user", display_name="报销员工", password_hash=hash_password("Password@123"), roles=[role])
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


def expense_login(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": "expense-user", "password": "Password@123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_expense_create_and_server_total(expense_client: TestClient):
    headers = expense_login(expense_client)
    response = expense_client.post("/api/v1/expenses", headers=headers, json={"title": "出差住宿", "category": "差旅费", "items": [{"description": "酒店", "amount": "380", "tax_amount": "22.8"}]})
    assert response.status_code == 200
    assert response.json()["data"]["total_amount"] == "402.80"
    assert response.json()["data"]["status"] == "DRAFT"


def test_expense_submit_and_optimistic_lock(expense_client: TestClient):
    headers = expense_login(expense_client)
    created = expense_client.post("/api/v1/expenses", headers=headers, json={"title": "交通费", "category": "差旅费", "items": [{"description": "打车", "amount": "80"}]}).json()["data"]
    submitted = expense_client.post(f"/api/v1/expenses/{created['id']}/submit", headers=headers, json={"expected_version": created["version"]})
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "SUBMITTED"
    conflict = expense_client.post(f"/api/v1/expenses/{created['id']}/submit", headers=headers, json={"expected_version": created["version"]})
    assert conflict.status_code == 409


def test_expense_cannot_update_after_submit(expense_client: TestClient):
    headers = expense_login(expense_client)
    created = expense_client.post("/api/v1/expenses", headers=headers, json={"title": "办公用品", "category": "办公费", "items": [{"description": "文具", "amount": "20"}]}).json()["data"]
    expense_client.post(f"/api/v1/expenses/{created['id']}/submit", headers=headers, json={"expected_version": created["version"]})
    response = expense_client.patch(f"/api/v1/expenses/{created['id']}", headers=headers, json={"title": "修改", "expected_version": 2})
    assert response.status_code == 409
