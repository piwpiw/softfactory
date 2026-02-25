"""
Test Configuration & Fixtures
SoftFactory Platform — Standard Test Suite
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.models import db as _db

TEST_DATABASE = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE
    os.environ["JWT_SECRET"] = "test-secret-key"

    app = create_app()

    # Apply test configuration after app creation
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Test database with rollback."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        yield _db
        transaction.rollback()
        connection.close()


@pytest.fixture
def demo_token():
    """Demo authentication token."""
    return "demo_token"


@pytest.fixture
def auth_headers(demo_token):
    """Authenticated request headers."""
    return {"Authorization": f"Bearer {demo_token}"}


@pytest.fixture
def admin_headers():
    """Admin request headers."""
    return {"Authorization": "Bearer admin_token_test"}
