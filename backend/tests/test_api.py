from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
    assert response.headers["x-request-id"]


def test_invoice_rule_passes():
    response = client.post("/api/v1/invoices/validate", json={"amount": "100", "tax_amount": "13", "total_amount": "113", "tax_rate": "0.13"})
    assert response.status_code == 200
    assert response.json()["data"]["passed"] is True


def test_invoice_rule_rejects_mismatch():
    response = client.post("/api/v1/invoices/validate", json={"amount": "100", "tax_amount": "13", "total_amount": "120", "tax_rate": "0.13"})
    assert response.status_code == 200
    assert response.json()["data"]["passed"] is False
