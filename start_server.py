import os
from pathlib import Path

# Local run always starts in development mode regardless of .env defaults.
os.environ['FLASK_ENV'] = 'development'
os.environ['ENVIRONMENT'] = 'development'
os.environ['DEBUG'] = 'true'
os.environ['TESTING'] = 'false'

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

# Normalize placeholders in .env before app creation
_db_url = os.getenv('DATABASE_URL', '')
if _db_url and '<' in _db_url:
    os.environ['DATABASE_URL'] = ''

_enc_key = os.getenv('ENCRYPTION_KEY', '')
if _enc_key and '<' in _enc_key:
    os.environ.pop('ENCRYPTION_KEY', None)

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
