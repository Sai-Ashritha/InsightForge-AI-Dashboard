import pytest
from fastapi.testclient import TestClient
import pandas as pd

from app.main import app
from app.auth import create_access_token
from app.database.orm import orm_create_user, orm_get_user_by_email, User
import app.routes.ml as ml_route
import app.routes.chat as chat_route
import app.routes.upload as upload_route

client = TestClient(app)


def test_auth_register_and_login(monkeypatch):
    test_email = "test_analyst@insightforge.ai"
    test_pass = "SecurePass123"

    class FakeUser:
        id = 99
        email = test_email
        hashed_password = "hashed_dummy_string"
        role = "analyst"
        is_active = True

    # Test registration endpoint
    monkeypatch.setattr("app.routes.auth.orm_get_user_by_email", lambda e: None)
    monkeypatch.setattr("app.routes.auth.orm_create_user", lambda e, p, r: FakeUser())

    reg_resp = client.post("/api/auth/register", json={"email": test_email, "password": test_pass, "role": "analyst"})
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == test_email

    # Test token endpoint
    monkeypatch.setattr("app.routes.auth.orm_get_user_by_email", lambda e: FakeUser())
    monkeypatch.setattr("app.routes.auth.verify_password", lambda p, h: True)

    login_resp = client.post("/api/auth/token", data={"username": test_email, "password": test_pass})
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["role"] == "analyst"


def test_upload_endpoint_performs_analysis_and_cleaning(monkeypatch):
    token = create_access_token("test@insightforge.ai", "analyst")
    sample_csv = (
        "date,product,category,region,quantity,unit_price,revenue\n"
        "2026-01-01,Widget A,Electronics,East,100,50,5000\n"
        "2026-01-01,Widget A,Electronics,East,100,50,5000\n"  # identical duplicate
        "2026-01-03,Widget B,Hardware,West,,30,3000\n"        # missing quantity
        "2026-01-04,Gadget X,Electronics,North,200,80,16000\n"
    )

    monkeypatch.setattr("app.routes.upload.save_uploaded_dataframe", lambda df: {"table": "sales", "inserted_rows": len(df)})

    response = client.post(
        "/api/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_sales.csv", sample_csv.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "raw_analysis" in data
    assert data["raw_analysis"]["rows"] == 4
    assert data["data_quality"]["quality_score"] > 0
    assert "cleaning_summary" in data
    assert data["cleaning_summary"]["duplicates_removed"] == 1
    assert data["cleaning_summary"]["missing_values_handled"] >= 1


def test_ml_endpoints(monkeypatch):
    token = create_access_token("test@insightforge.ai", "analyst")
    fake_sales = [
        {"date": f"2026-01-{i:02d}", "product": "Product A", "revenue": 1000 + i * 50, "quantity": 10 + i}
        for i in range(1, 25)
    ]
    monkeypatch.setattr(ml_route, "fetch_table", lambda t: fake_sales if t == "sales" else [])

    # Test ML Forecast
    f_resp = client.get("/api/ml/forecast", headers={"Authorization": f"Bearer {token}"})
    assert f_resp.status_code == 200
    f_data = f_resp.json()
    assert "forecast_data" in f_data
    assert "predicted_demand" in f_data
    assert "predicted_revenue" in f_data

    # Test ML Anomalies
    a_resp = client.get("/api/ml/anomalies", headers={"Authorization": f"Bearer {token}"})
    assert a_resp.status_code == 200
    assert a_resp.json()["algorithm"] == "Isolation Forest"

    # Test ML Sales Decline
    d_resp = client.get("/api/ml/sales-decline", headers={"Authorization": f"Bearer {token}"})
    assert d_resp.status_code == 200
    assert "declining_products" in d_resp.json()

    # Test ML Inventory
    i_resp = client.get("/api/ml/inventory", headers={"Authorization": f"Bearer {token}"})
    assert i_resp.status_code == 200
    assert "items" in i_resp.json()


def test_streaming_chat_endpoint(monkeypatch):
    token = create_access_token("test@insightforge.ai", "analyst")
    monkeypatch.setattr(chat_route, "fetch_table", lambda t: [
        {"date": "2026-01-01", "product": "Product A", "revenue": 50000, "quantity": 500}
    ])

    resp = client.post(
        "/api/chat/stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What should we manufacture next month?"},
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    content = resp.text
    assert "data: " in content
    assert "Analysis" in content or "manufacture" in content
