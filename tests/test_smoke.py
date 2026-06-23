"""Smoke test minimal: pastikan import & app factory jalan."""
from app import create_app


def test_app_factory():
    app = create_app("development")
    assert app is not None


def test_health_endpoint():
    app = create_app("development")
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
