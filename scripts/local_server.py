#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS Local Server - Team Access
로컬 + 로컬네트워크 팀 접근 가능
"""

from flask import Flask, Response, send_from_directory, jsonify, request
import socket
import subprocess
import json
from datetime import datetime, timedelta
from team_data import get_teams, get_team_summary, get_team_skills_matrix
from pathlib import Path

app = Flask(__name__, static_folder='../web')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTO_EXECUTION_ROOT = PROJECT_ROOT / "docs" / "plans" / "execution"
AUTO_FILE_WHITELIST = {
    "status.json",
    "status.md",
    "hourly_report.json",
    "hourly_report.md",
    "cycle_manifest.jsonl",
    "agent_5h_loop.log",
    "morning_check_brief.json",
    "morning_check_brief.md",
}

# 간단한 Rate Limiter
class SimpleRateLimiter:
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    def is_allowed(self, ip):
        now = datetime.now()
        if ip not in self.requests:
            self.requests[ip] = []

        # 윈도우 시간 밖의 요청 제거
        self.requests[ip] = [req_time for req_time in self.requests[ip]
                             if now - req_time < timedelta(seconds=self.window)]

        if len(self.requests[ip]) >= self.max_requests:
            return False

        self.requests[ip].append(now)
        return True

limiter = SimpleRateLimiter(max_requests=100, window=60)

# Network status check
def check_network():
    """네트워크 상태 체크"""
    try:
        result = subprocess.run(['ping', '-c' if 'linux' in subprocess.os.uname()[0].lower() else '-n', '1', '8.8.8.8'],
                              capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False

def get_local_ip():
    """로컬 IP 주소 가져오기"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

# Rate Limiting Middleware
def _safe_json_load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _find_latest_auto_run_dir():
    if not AUTO_EXECUTION_ROOT.exists():
        return None

    date_dirs = [
        p
        for p in AUTO_EXECUTION_ROOT.iterdir()
        if p.is_dir() and p.name and p.name[0].isdigit()
    ]
    if not date_dirs:
        return None

    date_dirs = sorted(date_dirs, key=lambda d: d.name, reverse=True)
    candidates = []
    for date_dir in date_dirs:
        for run_dir in sorted(date_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            if run_dir.name.lower().startswith("auto-"):
                candidates.append(run_dir)
        if candidates:
            break

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def _read_automation_status():
    run_dir = _find_latest_auto_run_dir()
    if not run_dir:
        return {
            "available": False,
            "run_dir": None,
            "status_file": None,
            "status": None,
        }

    status_path = run_dir / "status.json"
    status_payload = _safe_json_load(status_path, None)
    return {
        "available": status_payload is not None,
        "run_dir": str(run_dir),
        "status_file": str(status_path),
        "status": status_payload if isinstance(status_payload, dict) else None,
    }


def _read_cycle_manifest(limit: int = 10):
    run_dir = _find_latest_auto_run_dir()
    if not run_dir:
        return []

    manifest = run_dir / "cycle_manifest.jsonl"
    if not manifest.exists():
        return []

    lines = manifest.read_text(encoding="utf-8").splitlines()
    parsed = []
    for line in reversed(lines[-max(limit * 3, limit):]):
        if not line.strip():
            continue
        try:
            parsed.append(json.loads(line))
        except Exception:
            continue

    parsed = sorted(
        parsed,
        key=lambda item: _safe_int(item.get("iteration", 0), 0),
        reverse=True,
    )
    return parsed[:limit]


def _read_hourly_report():
    run_dir = _find_latest_auto_run_dir()
    if not run_dir:
        return None
    return _safe_json_load(run_dir / "hourly_report.json", None)

@app.before_request
def before_request():
    """모든 요청에 대해 Rate Limiting 체크"""
    ip = get_remote_address()
    if not limiter.is_allowed(ip):
        return jsonify({"error": "Rate limit exceeded"}), 429

def get_remote_address():
    """클라이언트 IP 가져오기"""
    return request.remote_addr or request.headers.get('X-Forwarded-For', '127.0.0.1')

# Routes - API routes MUST be defined before catch-all routes
@app.route('/api/v1/status')
def api_status():
    """시스템 상태 API"""
    return jsonify({
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "uptime": "99.98%",
        "error_rate": "0.02%",
        "latency": "145ms",
        "network": {
            "external": check_network(),
            "local_ip": get_local_ip(),
            "hostname": socket.gethostname()
        }
    })

@app.route('/api/v1/network')
def api_network():
    """네트워크 상태 체크"""
    external_ok = check_network()
    local_ip = get_local_ip()
    return jsonify({
        "external_network": "🟢 Connected" if external_ok else "🔴 No Connection",
        "local_ip": local_ip,
        "hostname": socket.gethostname(),
        "local_url": f"http://{local_ip}:5000",
        "localhost_url": "http://localhost:5000"
    })

@app.route('/api/v1/team-access')
def team_access():
    """팀 멤버 접근 정보"""
    local_ip = get_local_ip()
    return jsonify({
        "team_access": {
            "local": f"http://localhost:5000",
            "network": f"http://{local_ip}:5000",
            "external": "https://jarvis-production.up.railway.app (필요 시)",
            "status": "Ready"
        },
        "pages": {
            "homepage": "/",
            "operations": "/operations.html",
            "analytics": "/analytics.html",
            "teams": "/teams.html",
            "dashboard": "/dashboard.html",
            "automation_dashboard": "/automation-dashboard.html"
        }
    })

@app.route('/api/v1/teams')
def api_teams():
    """전체 팀 정보"""
    return jsonify({
        "teams": get_teams(),
        "summary": get_team_summary(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/teams/<team_id>')
def api_team_detail(team_id):
    """특정 팀 정보"""
    from team_data import get_team
    team = get_team(team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404
    return jsonify({
        "team": team,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/skills')
def api_skills():
    """스킬 매트릭스"""
    return jsonify({
        "skills_matrix": get_team_skills_matrix(),
        "timestamp": datetime.now().isoformat()
    })

# Automation status APIs
@app.route('/api/v1/automation/status')
def api_automation_status():
    return jsonify(_read_automation_status())


@app.route('/api/v1/automation/cycles')
def api_automation_cycles():
    try:
        limit = max(1, min(200, int(request.args.get("limit", "10"))))
    except ValueError:
        limit = 10
    run_dir = _find_latest_auto_run_dir()
    cycles = _read_cycle_manifest(limit)
    return jsonify({
        "run_dir": str(run_dir) if run_dir else None,
        "limit": limit,
        "count": len(cycles),
        "cycles": cycles,
    })


@app.route('/api/v1/automation/hourly')
def api_automation_hourly():
    payload = _read_hourly_report()
    return jsonify({
        "available": payload is not None,
        "items": payload.get("items", []) if isinstance(payload, dict) else [],
        "generated_at": payload.get("generated_at") if isinstance(payload, dict) else None,
    })


@app.route('/api/v1/automation/file')
def api_automation_file():
    file_name = request.args.get("name", "")
    if file_name not in AUTO_FILE_WHITELIST:
        return jsonify({"error": "Invalid file name"}), 400

    run_dir = _find_latest_auto_run_dir()
    if not run_dir:
        return jsonify({"error": "No automation run directory"}), 404

    target = run_dir / file_name
    if not target.exists():
        return jsonify({"error": "File not found"}), 404
    return Response(target.read_text(encoding="utf-8"), mimetype="text/plain; charset=utf-8")

# Static file routes - MUST come after all API routes
@app.route('/')
def index():
    return send_from_directory('../web', 'index.html')

@app.route('/<path:filename>')
def serve(filename):
    # 파일 경로 검증 (경로 탈출 방지)
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid file path"}), 400
    return send_from_directory('../web', filename)

if __name__ == '__main__':
    local_ip = get_local_ip()

    print("\n" + "="*60)
    print("JARVIS Local Server - Team Access")
    print("="*60)
    print(f"\n[Local Access]    http://localhost:5000")
    print(f"[Network Access]  http://{local_ip}:5000")
    print(f"\n[Team URLs]")
    print(f"   - Local:       http://localhost:5000")
    print(f"   - Network:     http://{local_ip}:5000")
    print(f"\n[Pages]")
    print(f"   - /                 (Homepage)")
    print(f"   - /operations.html  (Operations)")
    print(f"   - /analytics.html   (Analytics)")
    print(f"   - /teams.html       (Teams)")
    print(f"   - /dashboard.html   (Dashboard)")
    print(f"\n[API Endpoints]")
    print(f"   - /api/v1/status        (System Status)")
    print(f"   - /api/v1/network       (Network Status)")
    print(f"   - /api/v1/team-access   (Team Access Info)")
    print("\n" + "="*60 + "\n")

    # 0.0.0.0 바인드 = 모든 네트워크 인터페이스에서 접근 가능
    app.run(host='0.0.0.0', port=5000, debug=False)
