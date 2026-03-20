import os
import threading
from urllib.parse import parse_qsl, urlencode

_APP = None
_APP_LOCK = threading.Lock()


def _configure_runtime_env():
    is_vercel_runtime = bool(os.getenv("VERCEL", "").strip() == "1" or os.getenv("VERCEL_URL", "").strip())
    os.environ.setdefault("ENVIRONMENT", "production" if is_vercel_runtime else "development")
    os.environ.setdefault("TESTING", "false")
    os.environ.setdefault("DISABLE_ELASTICSEARCH", "1")
    os.environ.setdefault("SOFTFACTORY_DB_STRICT", "false")
    os.environ.setdefault("PLATFORM_SECRET_KEY", "softfactory-vercel-runtime-secret")

    db_url = (os.getenv("DATABASE_URL") or "").strip()
    if db_url.startswith("postgres://"):
        os.environ["DATABASE_URL"] = db_url.replace("postgres://", "postgresql://", 1)
        db_url = os.environ["DATABASE_URL"]

    allow_sqlite_fallback = os.getenv("SOFTFACTORY_ALLOW_SQLITE_RUNTIME_FALLBACK", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not db_url and not is_vercel_runtime and allow_sqlite_fallback:
        os.environ["DATABASE_URL"] = "sqlite:////tmp/softfactory-platform.db"
        return

    if not db_url and is_vercel_runtime:
        raise RuntimeError(
            "DATABASE_URL must be set for the Vercel runtime. "
            "Refusing to fall back to ephemeral /tmp SQLite in production."
        )


def _get_app():
    global _APP
    if _APP is None:
        with _APP_LOCK:
            if _APP is None:
                _configure_runtime_env()
                from backend.app import create_app
                from backend.models import init_db
                flask_app = create_app()
                init_db(flask_app)
                _APP = flask_app
    return _APP


def app(environ, start_response):
    flask_app = _get_app()

    query_pairs = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    forwarded_query = []
    raw_path = ""
    for key, value in query_pairs:
        if key == "path" and not raw_path:
            raw_path = value
            continue
        forwarded_query.append((key, value))

    target_path = "/" + raw_path.lstrip("/") if raw_path else "/"
    if not target_path.startswith("/api/"):
        target_path = "/api" + (target_path if target_path.startswith("/") else f"/{target_path}")

    environ["SCRIPT_NAME"] = ""
    environ["PATH_INFO"] = target_path
    environ["QUERY_STRING"] = urlencode(forwarded_query, doseq=True)

    return flask_app.wsgi_app(environ, start_response)
