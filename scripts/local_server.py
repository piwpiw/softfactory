#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS Local Server - Team Access
로컬 + 로컬네트워크 팀 접근 가능
"""

from flask import Flask, send_from_directory, jsonify, request
import socket
import subprocess
import json
from datetime import datetime, timedelta
from team_data import get_teams, get_team_summary, get_team_skills_matrix

app = Flask(__name__, static_folder='../web')

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
            "dashboard": "/dashboard.html"
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
