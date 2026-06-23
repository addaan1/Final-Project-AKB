"""Shared pytest fixtures."""
import sys
import pytest

# Add project root to path
sys.path.insert(0, ".")


@pytest.fixture
def app():
    """Flask app instance."""
    from app import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
