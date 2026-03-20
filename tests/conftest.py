"""
Test Configuration & Fixtures
SoftFactory Platform — Standard Test Suite
"""
import pytest
import os
import sys
from pathlib import Path
from types import SimpleNamespace

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

    # Override config for testing
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


@pytest.fixture(autouse=True)
def _cleanup_db(app):
    """Auto-cleanup: delete all rows from every table after each test."""
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


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
def auth_token(demo_token):
    """Legacy alias for tests expecting a raw bearer token string."""
    return demo_token


@pytest.fixture
def auth_headers(demo_token):
    """Authenticated request headers."""
    return {"Authorization": f"Bearer {demo_token}"}


@pytest.fixture
def user_headers(auth_headers):
    """Alias for tests expecting authenticated non-admin user headers."""
    return dict(auth_headers)


@pytest.fixture
def admin_headers():
    """Admin request headers."""
    return {"Authorization": "Bearer admin_token_test"}


@pytest.fixture
def test_user(app):
    """Create a reusable persisted test user with stable detached attributes."""
    from backend.models import db as models_db, User

    with app.app_context():
        user = User(
            email='shared-test-user@example.com',
            name='Shared Test User',
            email_verified=True
        )
        user.set_password('TestPassword123!')
        models_db.session.add(user)
        models_db.session.commit()
        models_db.session.refresh(user)
        payload = SimpleNamespace(id=user.id, email=user.email, name=user.name, role='user')
        return payload


def pytest_collection_modifyitems(config, items):
    """Auto-classify environment-dependent or long-running tests."""
    slow_file_markers = {
        "tests/test_encryption.py",
        "tests/test_feed_service.py",
        "tests/test_instagram_api.py",
        "tests/test_oauth.py",
        "tests/test_payment_advanced.py",
        "tests/test_payment_system.py",
        "tests/test_review_api_v2.py",
        "tests/test_sns_revenue_api.py",
        "tests/test_telegram_integration.py",
        "tests/integration/test_auth_oauth.py",
        "tests/integration/test_error_paths.py",
        "tests/integration/test_review_endpoints.py",
        "tests/integration/test_review_scrapers_integration.py",
        "tests/integration/test_review_service.py",
        "tests/integration/test_scraper_integration.py",
        "tests/integration/test_services.py",
        "tests/integration/test_sns_advanced.py",
        "tests/integration/test_sns_auto_endpoints.py",
        "tests/integration/test_sns_endpoints.py",
        "tests/integration/test_sns_monetize.py",
        "tests/integration/test_twitter_api.py",
        "tests/integration/test_twitter_endpoints.py",
        "tests/integration/test_workflows.py",
    }

    for item in items:
        path = Path(str(item.fspath)).as_posix()
        nodeid = item.nodeid.lower()

        if "/tests/e2e/" in f"/{path}" or path.endswith("/tests/test_accessibility.py"):
            item.add_marker(pytest.mark.e2e)

        if (
            "testperformance" in nodeid
            or "performance" in nodeid
            or "response_time" in nodeid
            or "benchmark" in nodeid
            or path.endswith(tuple(slow_file_markers))
        ):
            item.add_marker(pytest.mark.slow)
