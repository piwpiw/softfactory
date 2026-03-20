#!/usr/bin/env python
"""Compatibility entrypoint for platforms expecting run.py."""

from start_server import app

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", os.environ.get("APP_PORT", "8000")))
    debug = os.environ.get("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
    print(f"[run.py] environment={os.environ.get('ENVIRONMENT', 'development')} debug={str(debug).lower()} port={port}")
    print(f"[run.py] health=http://127.0.0.1:{port}/health")
    print(f"[run.py] log_file={os.environ.get('LOG_FILE', '')}")
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
