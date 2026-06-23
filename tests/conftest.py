"""Shared pytest fixtures."""
import sys
import pytest

# Add project root to path
sys.path.insert(0, ".")


@pytest.fixture(autouse=True)
def reset_users_package():
    """Reset demo user package to 'free' before each test (avoid contamination)."""
    from app.auth import find_user_by_email, update_user_package
    demo = find_user_by_email("demo@galbay.id")
    if demo and demo.is_premium:
        update_user_package(demo.id, "free")
    yield
    demo = find_user_by_email("demo@galbay.id")
    if demo and demo.is_premium:
        update_user_package(demo.id, "free")


@pytest.fixture
def app():
    """Flask app instance."""
    from app import create_app
    application = create_app("development")
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    return application


@pytest.fixture
def client(app):
    """Flask test client (unauthenticated)."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Flask test client with logged-in demo user (free)."""
    client.post("/login", data={
        "action": "demo",
        "email": "demo@galbay.id",
        "password": "demo123",
    })
    return client


@pytest.fixture
def premium_client(app, client):
    """Flask test client with logged-in premium demo user."""
    client.post("/login", data={
        "action": "demo",
        "email": "premium@galbay.id",
        "password": "demo123",
    })
    return client
