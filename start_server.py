import os
from pathlib import Path
from backend.config import Config
from backend.runtime_paths import default_app_log_path

# Local run defaults (do not override environment-provided settings).
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('DEBUG', 'true')
os.environ.setdefault('TESTING', 'false')

# Load .env for local/dev execution (keeps service keys/urls while
# preserving environment override above)
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            env_key = key.strip()
            env_val = value.strip().strip('"\'')
            if env_key in ('FLASK_ENV', 'ENVIRONMENT', 'DEBUG', 'TESTING'):
                continue
            os.environ.setdefault(env_key, env_val)

_db_url = Config.get_database_url()
if _db_url:
    os.environ['DATABASE_URL'] = _db_url
else:
    os.environ['DATABASE_URL'] = ''

_enc_key = os.getenv('ENCRYPTION_KEY', '')
if _enc_key and '<' in _enc_key:
    os.environ.pop('ENCRYPTION_KEY', None)

os.environ.setdefault('LOG_FILE', str(default_app_log_path()))

from backend.app import create_app

app = create_app()


def _log_startup(port: int, debug: bool) -> None:
    env = os.getenv("ENVIRONMENT", "development")
    print(f"[start_server] environment={env} debug={str(debug).lower()} port={port}")
    print(f"[start_server] health=http://127.0.0.1:{port}/health")
    print(f"[start_server] api_health=http://127.0.0.1:{port}/api/health")
    print(f"[start_server] platform_index=http://127.0.0.1:{port}/web/platform/index.html")
    print(f"[start_server] log_file={os.environ.get('LOG_FILE')}")

if __name__ == '__main__':
    port = int(os.getenv("PORT", os.getenv("APP_PORT", "8000")))
    debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
    _log_startup(port, debug)
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True,
        use_reloader=debug
    )
