import pytest

from api.runtime import _configure_runtime_env
from backend.app import create_app


def test_vercel_runtime_requires_database_url(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("VERCEL_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("SOFTFACTORY_ALLOW_SQLITE_RUNTIME_FALLBACK", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
        _configure_runtime_env()


def test_health_exposes_database_backend_label(monkeypatch, tmp_path):
    db_path = tmp_path / "health-backend.db"

    monkeypatch.setenv("TESTING", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("DISABLE_ELASTICSEARCH", "1")

    app = create_app()
    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code in (200, 503)
    payload = response.get_json()
    assert payload["database_backend"] == "sqlite"
