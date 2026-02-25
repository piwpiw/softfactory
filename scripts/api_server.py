#!/usr/bin/env python3
"""
🤖 JARVIS API Server — RESTful Backend for CooCook Operations
Provides REST endpoints for web dashboard control
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone
import json
import os
from pathlib import Path

# Flask 앱 초기화 (static 파일 서빙)
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'web'), static_url_path='')
CORS(app)

# ============================================================================
# DATA MODELS
# ============================================================================

TEAMS = {
    "01": {"name": "Chief Dispatcher", "icon": "🧭", "skills": 3, "total_skills": 5, "percent": 60},
    "02": {"name": "Product Manager", "icon": "📋", "skills": 3, "total_skills": 6, "percent": 50},
    "03": {"name": "Market Analyst", "icon": "📊", "skills": 3, "total_skills": 6, "percent": 50},
    "04": {"name": "Solution Architect", "icon": "🏗️", "skills": 4, "total_skills": 7, "percent": 57},
    "05": {"name": "Backend Developer", "icon": "⚙️", "skills": 3, "total_skills": 8, "percent": 37},
    "06": {"name": "Frontend Developer", "icon": "🎨", "skills": 2, "total_skills": 7, "percent": 28},
    "07": {"name": "QA Engineer", "icon": "🔍", "skills": 1, "total_skills": 7, "percent": 14},
    "08": {"name": "Security Auditor", "icon": "🔐", "skills": 3, "total_skills": 7, "percent": 42},
    "09": {"name": "DevOps Engineer", "icon": "🚀", "skills": 1, "total_skills": 7, "percent": 14},
    "10": {"name": "Telegram Reporter", "icon": "📣", "skills": 3, "total_skills": 7, "percent": 42},
}

MISSIONS = {
    "M-001": {
        "id": "M-001",
        "name": "Initial Infrastructure Setup",
        "status": "COMPLETE",
        "priority": "P1",
        "started": "2026-02-22",
        "progress": 100,
        "teams": ["01", "04", "09"],
        "points": 25,
    },
    "M-002": {
        "id": "M-002",
        "name": "CooCook Market Analysis & Launch",
        "status": "IN_PROGRESS",
        "priority": "P1",
        "started": "2026-02-22",
        "progress": 60,
        "teams": ["02", "03", "04", "05", "06"],
        "points": 20,
    },
}

SPRINTS = {
    "S-001": {
        "id": "S-001",
        "name": "Auth System Sprint",
        "status": "IN_PROGRESS",
        "start": "2026-02-23",
        "end": "2026-03-08",
        "capacity": 40,
        "completed": 12,
        "tasks": [
            {
                "id": "T-001",
                "name": "JWT Authentication",
                "team": "05",
                "points": 5,
                "progress": 60,
                "status": "IN_PROGRESS",
            },
            {
                "id": "T-003",
                "name": "Login UI",
                "team": "06",
                "points": 5,
                "progress": 40,
                "status": "IN_PROGRESS",
            },
            {
                "id": "T-004",
                "name": "API Tests",
                "team": "07",
                "points": 2,
                "progress": 0,
                "status": "BACKLOG",
            },
        ],
    },
}

DEPLOYS = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_utc_time():
    """Get current UTC time"""
    return datetime.now(timezone.utc)

def get_operation_phase():
    """Determine current operation phase based on UTC hour"""
    hour = get_utc_time().hour
    phases = {
        9: "🎙️ STANDUP",
        10: "🚀 PROJECT_LAUNCH",
        13: "📊 SPRINT_REVIEW",
        15: "🧪 STAGING_DEPLOY",
        17: "🌍 PROD_DEPLOY",
        18: "📝 SUMMARY",
    }
    if hour in phases:
        return phases[hour]
    elif 9 <= hour < 18:
        return "⚙️ WORKING_HOURS"
    else:
        return "🌙 OFF_HOURS"

def format_progress_bar(percent: int, length: int = 10) -> str:
    """Format progress bar: 30% ▓▓▓░░░░░░"""
    filled = int(length * percent / 100)
    bar = "▓" * filled + "░" * (length - filled)
    return f"{percent}% {bar}"

# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@app.route("/api/v1/status", methods=["GET"])
def get_status():
    """Get overall system status"""
    total_skills = sum(t["total_skills"] for t in TEAMS.values())
    active_skills = sum(t["skills"] for t in TEAMS.values())
    avg_percent = int(sum(t["percent"] for t in TEAMS.values()) / len(TEAMS))

    return jsonify({
        "timestamp": get_utc_time().isoformat(),
        "operation_phase": get_operation_phase(),
        "missions": {
            "total": len(MISSIONS),
            "in_progress": sum(1 for m in MISSIONS.values() if m["status"] == "IN_PROGRESS"),
            "completed": sum(1 for m in MISSIONS.values() if m["status"] == "COMPLETE"),
        },
        "sprints": {
            "active": list(SPRINTS.keys()),
            "progress": f"{SPRINTS['S-001']['completed']}/{SPRINTS['S-001']['capacity']} points",
        },
        "teams": {
            "total": len(TEAMS),
            "overall_skill_level": f"{avg_percent}%",
            "active_skills": active_skills,
            "total_skills": total_skills,
        },
    })

@app.route("/api/v1/teams", methods=["GET"])
def get_teams():
    """Get all teams with their skill status"""
    return jsonify({
        "teams": [
            {
                "id": team_id,
                "name": data["name"],
                "icon": data["icon"],
                "skill_percent": data["percent"],
                "progress_bar": format_progress_bar(data["percent"]),
                "skills": f"{data['skills']}/{data['total_skills']}",
                "status": "ACTIVE" if data["percent"] >= 50 else "NEEDS_UPGRADE",
            }
            for team_id, data in sorted(TEAMS.items())
        ]
    })

@app.route("/api/v1/teams/<team_id>", methods=["GET"])
def get_team(team_id):
    """Get specific team details"""
    if team_id not in TEAMS:
        return jsonify({"error": "Team not found"}), 404

    team = TEAMS[team_id]
    return jsonify({
        "id": team_id,
        "name": team["name"],
        "icon": team["icon"],
        "skill_level": f"{team['percent']}%",
        "progress_bar": format_progress_bar(team["percent"]),
        "active_skills": team["skills"],
        "total_skills": team["total_skills"],
        "status": "ACTIVE" if team["percent"] >= 50 else "NEEDS_UPGRADE",
    })

@app.route("/api/v1/missions", methods=["GET"])
def get_missions():
    """Get all missions"""
    return jsonify({
        "missions": [
            {
                "id": m["id"],
                "name": m["name"],
                "status": m["status"],
                "priority": m["priority"],
                "progress": m["progress"],
                "progress_bar": format_progress_bar(m["progress"]),
                "started": m["started"],
                "teams": len(m["teams"]),
                "points": m["points"],
            }
            for m in MISSIONS.values()
        ]
    })

@app.route("/api/v1/missions/<mission_id>", methods=["GET"])
def get_mission(mission_id):
    """Get specific mission details"""
    if mission_id not in MISSIONS:
        return jsonify({"error": "Mission not found"}), 404

    m = MISSIONS[mission_id]
    return jsonify({
        "id": m["id"],
        "name": m["name"],
        "status": m["status"],
        "priority": m["priority"],
        "progress": m["progress"],
        "progress_bar": format_progress_bar(m["progress"]),
        "started": m["started"],
        "teams": [TEAMS[tid]["name"] for tid in m["teams"]],
        "points": m["points"],
    })

@app.route("/api/v1/sprints", methods=["GET"])
def get_sprints():
    """Get all active sprints"""
    return jsonify({
        "sprints": [
            {
                "id": s["id"],
                "name": s["name"],
                "status": s["status"],
                "start": s["start"],
                "end": s["end"],
                "progress": f"{s['completed']}/{s['capacity']}",
                "progress_bar": format_progress_bar(int(s["completed"] / s["capacity"] * 100)),
                "tasks_count": len(s["tasks"]),
            }
            for s in SPRINTS.values()
        ]
    })

@app.route("/api/v1/sprints/<sprint_id>", methods=["GET"])
def get_sprint(sprint_id):
    """Get specific sprint details"""
    if sprint_id not in SPRINTS:
        return jsonify({"error": "Sprint not found"}), 404

    s = SPRINTS[sprint_id]
    return jsonify({
        "id": s["id"],
        "name": s["name"],
        "status": s["status"],
        "start": s["start"],
        "end": s["end"],
        "capacity": s["capacity"],
        "completed": s["completed"],
        "progress_bar": format_progress_bar(int(s["completed"] / s["capacity"] * 100)),
        "tasks": [
            {
                "id": t["id"],
                "name": t["name"],
                "team": TEAMS[t["team"]]["name"],
                "points": t["points"],
                "progress": t["progress"],
                "progress_bar": format_progress_bar(t["progress"]),
                "status": t["status"],
            }
            for t in s["tasks"]
        ],
    })

# ============================================================================
# ACTION ENDPOINTS
# ============================================================================

@app.route("/api/v1/missions", methods=["POST"])
def create_mission():
    """Create new mission"""
    data = request.json or {}
    name = data.get("name", "Untitled Mission")
    priority = data.get("priority", "P2")

    # Generate mission ID
    mission_id = f"M-{int(max(m.split('-')[1] for m in MISSIONS.keys())) + 1:03d}"

    mission = {
        "id": mission_id,
        "name": name,
        "status": "PLANNING",
        "priority": priority,
        "started": get_utc_time().strftime("%Y-%m-%d"),
        "progress": 0,
        "teams": ["02", "03", "04"],  # Auto-assigned
        "points": 0,
    }

    MISSIONS[mission_id] = mission

    return jsonify({
        "status": "created",
        "mission": mission,
        "message": f"✅ Mission {mission_id} created. Teams assigned: PM, Analyst, Architect",
    }), 201

@app.route("/api/v1/deploy/staging", methods=["POST"])
def deploy_staging():
    """Deploy to staging"""
    data = request.json or {}
    version = data.get("version", "v1.0.0")

    deploy = {
        "id": len(DEPLOYS) + 1,
        "type": "STAGING",
        "version": version,
        "status": "IN_PROGRESS",
        "timestamp": get_utc_time().isoformat(),
        "progress": 0,
    }
    DEPLOYS.append(deploy)

    return jsonify({
        "status": "started",
        "deploy": deploy,
        "message": f"🧪 Deploying {version} to staging environment",
    }), 202

@app.route("/api/v1/deploy/prod", methods=["POST"])
def deploy_prod():
    """Deploy to production"""
    data = request.json or {}
    version = data.get("version", "v1.0.0")

    # Check for confirmation
    if not data.get("confirmed", False):
        return jsonify({
            "error": "confirmation_required",
            "message": f"🌍 Production deployment requires confirmation for {version}",
        }), 400

    deploy = {
        "id": len(DEPLOYS) + 1,
        "type": "PRODUCTION",
        "version": version,
        "status": "IN_PROGRESS",
        "timestamp": get_utc_time().isoformat(),
        "progress": 0,
    }
    DEPLOYS.append(deploy)

    return jsonify({
        "status": "started",
        "deploy": deploy,
        "message": f"🚀 Deploying {version} to production with blue-green strategy",
    }), 202

@app.route("/api/v1/standup", methods=["POST"])
def create_standup():
    """Generate daily standup report"""
    standup_report = {
        "timestamp": get_utc_time().isoformat(),
        "date": get_utc_time().strftime("%Y-%m-%d"),
        "teams": []
    }

    team_reports = {
        "05": {
            "name": "Team 05: Backend Developer",
            "yesterday": "JWT auth completed",
            "today": "User API implementation",
            "blocker": None,
        },
        "06": {
            "name": "Team 06: Frontend Developer",
            "yesterday": "Login UI 50% done",
            "today": "Dashboard UI",
            "blocker": "Waiting for API spec",
        },
        "09": {
            "name": "Team 09: DevOps Engineer",
            "yesterday": "Staging environment ready",
            "today": "Blue-Green deployment setup",
            "blocker": None,
        },
    }

    for team_id, report in team_reports.items():
        standup_report["teams"].append({
            "team_id": team_id,
            "name": report["name"],
            "yesterday": f"✅ {report['yesterday']}",
            "today": f"🔄 {report['today']}",
            "blocker": f"🚨 {report['blocker']}" if report['blocker'] else "🚨 None",
        })

    return jsonify(standup_report), 200

@app.route("/api/v1/summary", methods=["POST"])
def create_summary():
    """Generate daily summary report"""
    summary = {
        "timestamp": get_utc_time().isoformat(),
        "date": get_utc_time().strftime("%Y-%m-%d"),
        "achievements": {
            "features_deployed": 1,
            "bugs_fixed": 3,
            "users_affected": 10234,
            "performance_improvement": "+8%",
        },
        "metrics": {
            "new_prs": 12,
            "merged_prs": 8,
            "code_reviews": 15,
            "test_coverage": "89%",
            "incidents": 0,
        },
        "team_performance": {
            "05": {"name": "Backend Dev", "points": 8, "target": 8, "status": "✓ ON_TARGET"},
            "06": {"name": "Frontend Dev", "points": 5, "target": 6, "status": "⚠️ BELOW_TARGET"},
            "07": {"name": "QA Engineer", "points": 3, "target": 3, "status": "✓ ON_TARGET"},
            "09": {"name": "DevOps", "points": 2, "target": 2, "status": "✓ ON_TARGET"},
        },
        "nps_impact": {
            "yesterday": 54,
            "today": 56,
            "change": "+2 ⬆️",
        },
        "next_steps": [
            "Start 1 new project",
            "Target Sprint progress: 40%",
            "Prepare v1.2.25 deployment",
        ],
    }

    return jsonify(summary), 200

@app.route("/api/v1/teams/<team_id>/upgrade", methods=["POST"])
def upgrade_team(team_id):
    """Upgrade team skills"""
    if team_id not in TEAMS:
        return jsonify({"error": "Team not found"}), 404

    team = TEAMS[team_id]
    blocked_skills = team["total_skills"] - team["skills"]

    if blocked_skills == 0:
        return jsonify({
            "status": "already_complete",
            "message": f"Team {team_id} is already at maximum skill level",
        }), 200

    # Simulate upgrade
    upgrade_plan = {
        "team_id": team_id,
        "team_name": team["name"],
        "skills_to_install": blocked_skills,
        "current_level": f"{team['percent']}%",
        "target_level": "100%",
        "estimated_time": "30 minutes",
        "status": "QUEUED",
    }

    return jsonify(upgrade_plan), 202

# ============================================================================
# HEALTH & DIAGNOSTICS
# ============================================================================

@app.route("/api/v1/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": get_utc_time().isoformat(),
        "version": "1.0",
        "operation_phase": get_operation_phase(),
    }), 200

@app.route("/", methods=["GET"])
def root():
    """Serve operations dashboard"""
    try:
        with open(os.path.join(app.static_folder, 'operations.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "name": "🤖 JARVIS API Server",
            "version": "1.0",
            "description": "RESTful API for CooCook operations management",
            "status": "running",
            "endpoints": {
                "status": "GET /api/v1/status",
                "teams": "GET /api/v1/teams",
                "missions": "GET /api/v1/missions",
                "sprints": "GET /api/v1/sprints",
                "deploy_staging": "POST /api/v1/deploy/staging",
                "deploy_prod": "POST /api/v1/deploy/prod",
                "standup": "POST /api/v1/standup",
                "summary": "POST /api/v1/summary",
            },
        })

@app.route("/<path:filename>", methods=["GET"])
def serve_static(filename):
    """Serve static files (HTML, CSS, JS)"""
    try:
        return send_from_directory(app.static_folder, filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    print(f"""
    ╔════════════════════════════════════════════════╗
    ║   🤖 JARVIS API Server v1.0                     ║
    ║   CooCook Operations Management                 ║
    ╚════════════════════════════════════════════════╝

    🚀 Starting on http://0.0.0.0:{port}
    📚 API Docs: http://0.0.0.0:{port}/
    🔌 CORS: Enabled for web dashboard
    🌍 Environment: {'Development' if debug else 'Production'}

    Press Ctrl+C to stop
    """)

    app.run(host="0.0.0.0", port=port, debug=debug)
