#!/usr/bin/env python
"""SoftFactory Platform Entry Point"""
import sys
import os
from pathlib import Path

# Load .env file manually
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

from backend.app import create_app

# For gunicorn / WSGI
# gunicorn uses this module-level `app` object when invoked as:
#   gunicorn "start_platform:app"
# The __main__ block below is only executed for local development.
app = create_app()

if __name__ == '__main__':
    # `app` is already created above (module-level) — reuse it for dev server
    print("\n" + "="*70)
    print("SoftFactory Platform Starting...")
    print("="*70)
    print("\nDEMO MODE (No Backend Needed):")
    print("  Login Page:  http://localhost:9000/web/platform/login.html")
    print("  Passkey:     demo2026")
    print("  All features work with mock data!")
    print("\nMain Services:")
    print("  Dashboard:        http://localhost:9000/web/platform/index.html")
    print("  CooCook:          http://localhost:9000/web/coocook/index.html")
    print("  SNS Auto:         http://localhost:9000/web/sns-auto/index.html")
    print("  Review Campaign:  http://localhost:9000/web/review/index.html")
    print("  AI Automation:    http://localhost:9000/web/ai-automation/index.html")
    print("  WebApp Builder:   http://localhost:9000/web/webapp-builder/index.html")
    print("\nAPI:")
    print("  Base URL:    http://localhost:9000/api/")
    print("\nDemo Users:")
    print("  Admin:  admin@softfactory.com / admin123")
    print("  Demo:   demo@softfactory.com / demo123")
    print("\nDocumentation:")
    print("  Demo Guide:  D:/Project/DEMO_GUIDE.md")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=9000, debug=False)
