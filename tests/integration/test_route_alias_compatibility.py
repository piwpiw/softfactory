import os

from backend.app import create_app


def _make_client(tmp_path):
    db_path = tmp_path / "alias_compat.db"
    os.environ["TESTING"] = "false"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_alias_routes_are_registered_for_frontend_clients(tmp_path):
    client = _make_client(tmp_path)

    checks = [
        ("get", "/api/sns/link-in-bio"),
        ("get", "/api/sns/link-in-bio/1"),
        ("get", "/api/sns/link-in-bio/1/stats"),
        ("get", "/api/review/auto-apply/rules"),
        ("post", "/api/review/auto-apply/run"),
        ("get", "/api/telegram/status"),
    ]

    for method, path in checks:
        response = getattr(client, method)(path)
        assert response.status_code != 404, path
