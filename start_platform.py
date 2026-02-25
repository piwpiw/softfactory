#!/usr/bin/env python
"""SoftFactory Platform Entry Point"""
import sys
from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*70)
    print("SoftFactory Platform Starting...")
    print("="*70)
    print("\nDEMO MODE (No Backend Needed):")
    print("  Login Page:  http://localhost:8000/web/platform/login.html")
    print("  Passkey:     demo2026")
    print("  All features work with mock data!")
    print("\nMain Services:")
    print("  Dashboard:        http://localhost:8000/web/platform/index.html")
    print("  CooCook:          http://localhost:8000/web/coocook/index.html")
    print("  SNS Auto:         http://localhost:8000/web/sns-auto/index.html")
    print("  Review Campaign:  http://localhost:8000/web/review/index.html")
    print("  AI Automation:    http://localhost:8000/web/ai-automation/index.html")
    print("  WebApp Builder:   http://localhost:8000/web/webapp-builder/index.html")
    print("\nAPI:")
    print("  Base URL:    http://localhost:8000/api/")
    print("\nDemo Users:")
    print("  Admin:  admin@softfactory.com / admin123")
    print("  Demo:   demo@softfactory.com / demo123")
    print("\nDocumentation:")
    print("  Demo Guide:  D:/Project/DEMO_GUIDE.md")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=8000, debug=True)
