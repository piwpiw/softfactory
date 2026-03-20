import os

from backend.app import create_app
from backend.services.elasticsearch_service import search_manager


def test_create_app_can_be_called_twice_without_schema_crash(tmp_path):
    db_path = tmp_path / "reentry.db"

    os.environ["TESTING"] = "false"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["DISABLE_ELASTICSEARCH"] = "1"

    app_one = create_app()
    app_two = create_app()

    with app_one.test_client() as client_one:
        res_one = client_one.get("/api/health")
        assert res_one.status_code in (200, 503)

    with app_two.test_client() as client_two:
        res_two = client_two.get("/api/health")
        assert res_two.status_code in (200, 503)


def test_testing_mode_skips_elasticsearch_initialization(tmp_path):
    db_path = tmp_path / "testing-es.db"

    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["DISABLE_ELASTICSEARCH"] = "1"

    app = create_app()

    assert app.config["TESTING"] is True
    assert search_manager is None
