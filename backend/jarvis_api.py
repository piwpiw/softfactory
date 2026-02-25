"""JARVIS Multi-Agent System API Routes"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json

jarvis_bp = Blueprint('jarvis', __name__, url_prefix='/api/v1')

# Mock team data (in production, this would come from database)
TEAMS_DATA = [
    {'id': 1, 'name': 'Team 01 — Dispatcher', 'progress': 85, 'skills': 8, 'status': 'active', 'color': '#10b981'},
    {'id': 2, 'name': 'Team 02 — Product Manager', 'progress': 72, 'skills': 7, 'status': 'active', 'color': '#3b82f6'},
    {'id': 3, 'name': 'Team 03 — Market Analyst', 'progress': 65, 'skills': 6, 'status': 'active', 'color': '#f59e0b'},
    {'id': 4, 'name': 'Team 04 — Architect', 'progress': 78, 'skills': 7, 'status': 'active', 'color': '#8b5cf6'},
    {'id': 5, 'name': 'Team 05 — Backend Dev', 'progress': 62, 'skills': 5, 'status': 'progress', 'color': '#ec4899'},
    {'id': 6, 'name': 'Team 06 — Frontend Dev', 'progress': 58, 'skills': 5, 'status': 'progress', 'color': '#14b8a6'},
    {'id': 7, 'name': 'Team 07 — QA Engineer', 'progress': 45, 'skills': 4, 'status': 'progress', 'color': '#06b6d4'},
    {'id': 8, 'name': 'Team 08 — Security Auditor', 'progress': 35, 'skills': 3, 'status': 'pending', 'color': '#f87171'},
    {'id': 9, 'name': 'Team 09 — DevOps Engineer', 'progress': 28, 'skills': 2, 'status': 'pending', 'color': '#fbbf24'},
    {'id': 10, 'name': 'Team 10 — Telegram Reporter', 'progress': 15, 'skills': 1, 'status': 'pending', 'color': '#a78bfa'}
]

MILESTONES = [
    {'date': '2026-02-25', 'title': 'Governance v3.0 배포', 'status': 'complete'},
    {'date': '2026-02-27', 'title': 'Team 05-06 QA 검증', 'status': 'in_progress'},
    {'date': '2026-03-01', 'title': '전체 통합 테스트', 'status': 'pending'},
    {'date': '2026-03-15', 'title': 'Production 배포', 'status': 'pending'}
]


@jarvis_bp.route('/teams', methods=['GET'])
def get_teams():
    """Get all 10 teams with progress"""
    return jsonify({
        'teams': TEAMS_DATA,
        'total_teams': len(TEAMS_DATA),
        'active_teams': len([t for t in TEAMS_DATA if t['status'] == 'active']),
        'total_skills': sum(t['skills'] for t in TEAMS_DATA),
        'avg_progress': round(sum(t['progress'] for t in TEAMS_DATA) / len(TEAMS_DATA), 1),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@jarvis_bp.route('/teams/stream', methods=['GET'])
def teams_stream():
    """Server-Sent Events (SSE) for real-time team updates"""
    def generate():
        while True:
            # Simulate team progress updates
            updated_teams = []
            for team in TEAMS_DATA:
                team_copy = team.copy()
                if team_copy['progress'] < 100:
                    team_copy['progress'] = min(100, team_copy['progress'] + (1 if team_copy['status'] != 'pending' else 0))
                updated_teams.append(team_copy)

            event_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'teams': updated_teams,
                'avg_progress': round(sum(t['progress'] for t in updated_teams) / len(updated_teams), 1)
            }

            yield f"data: {json.dumps(event_data)}\n\n"

            # Sleep would go here in real implementation
            # import time
            # time.sleep(5)
            break

    return generate(), 200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    }


@jarvis_bp.route('/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    """Get specific team details"""
    team = next((t for t in TEAMS_DATA if t['id'] == team_id), None)
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    return jsonify({
        'team': team,
        'skills_breakdown': {
            'completed': team['skills'],
            'in_progress': max(0, 7 - team['skills']),
            'pending': 0
        },
        'timeline': [
            {'date': '2026-02-25', 'event': 'Team initialized', 'status': 'complete'},
            {'date': '2026-02-27', 'event': 'Phase 1 checkpoint', 'status': 'pending'},
            {'date': '2026-03-01', 'event': 'Phase 2 review', 'status': 'pending'}
        ]
    }), 200


@jarvis_bp.route('/teams/breakdown', methods=['GET'])
def teams_breakdown():
    """Get detailed team analysis with capacity and bottlenecks"""
    high_capacity = [t for t in TEAMS_DATA if t['progress'] >= 70]
    medium_capacity = [t for t in TEAMS_DATA if 50 <= t['progress'] < 70]
    low_capacity = [t for t in TEAMS_DATA if t['progress'] < 50]

    return jsonify({
        'capacity_analysis': {
            'high_capacity': {
                'count': len(high_capacity),
                'teams': high_capacity,
                'avg_progress': round(sum(t['progress'] for t in high_capacity) / len(high_capacity), 1) if high_capacity else 0
            },
            'medium_capacity': {
                'count': len(medium_capacity),
                'teams': medium_capacity,
                'avg_progress': round(sum(t['progress'] for t in medium_capacity) / len(medium_capacity), 1) if medium_capacity else 0
            },
            'low_capacity': {
                'count': len(low_capacity),
                'teams': low_capacity,
                'avg_progress': round(sum(t['progress'] for t in low_capacity) / len(low_capacity), 1) if low_capacity else 0
            }
        },
        'bottlenecks': [
            {'team': 'Team 05 (Backend)', 'issue': 'Low progress (62%)', 'impact': 'High', 'recommendation': 'Allocate senior resources'},
            {'team': 'Team 06 (Frontend)', 'issue': 'Blocked by backend', 'impact': 'High', 'recommendation': 'Parallel API spec'},
            {'team': 'Team 08-10', 'issue': 'Not started', 'impact': 'Medium', 'recommendation': 'Pending earlier phases'}
        ],
        'skill_distribution': {
            'total_skills': sum(t['skills'] for t in TEAMS_DATA),
            'max_skills': max(t['skills'] for t in TEAMS_DATA),
            'min_skills': min(t['skills'] for t in TEAMS_DATA),
            'avg_skills': round(sum(t['skills'] for t in TEAMS_DATA) / len(TEAMS_DATA), 1)
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@jarvis_bp.route('/teams/timeline', methods=['GET'])
def teams_timeline():
    """Get milestone timeline and critical path"""
    return jsonify({
        'milestones': MILESTONES,
        'critical_path': [
            'Team 01 Dispatcher — Setup',
            'Team 04 Architect — Design',
            'Team 05 Backend — Implementation (BOTTLENECK)',
            'Team 06 Frontend — Integration',
            'Team 07 QA — Validation',
            'Team 09 DevOps — Deployment'
        ],
        'project_timeline': {
            'start_date': '2026-02-22',
            'target_completion': '2026-03-15',
            'days_remaining': 21,
            'phases': [
                {'name': 'Planning & Design', 'progress': 100, 'end_date': '2026-02-25'},
                {'name': 'Development', 'progress': 35, 'end_date': '2026-03-01'},
                {'name': 'Testing & QA', 'progress': 0, 'end_date': '2026-03-10'},
                {'name': 'Deployment', 'progress': 0, 'end_date': '2026-03-15'}
            ]
        },
        'next_milestone': 'Team 05-06 QA Validation (2026-02-27)',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@jarvis_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get comprehensive system statistics"""
    active_teams = len([t for t in TEAMS_DATA if t['status'] == 'active'])
    progress_teams = len([t for t in TEAMS_DATA if t['status'] == 'progress'])
    pending_teams = len([t for t in TEAMS_DATA if t['status'] == 'pending'])

    return jsonify({
        'summary': {
            'total_teams': 10,
            'active_teams': active_teams,
            'in_progress_teams': progress_teams,
            'pending_teams': pending_teams,
            'total_skills': 70,
            'completed_skills': sum(t['skills'] for t in TEAMS_DATA),
            'overall_progress': round(sum(t['progress'] for t in TEAMS_DATA) / len(TEAMS_DATA), 1)
        },
        'by_status': {
            'active': active_teams,
            'progress': progress_teams,
            'pending': pending_teams
        },
        'top_performers': sorted(TEAMS_DATA, key=lambda x: x['progress'], reverse=True)[:3],
        'needs_attention': sorted(TEAMS_DATA, key=lambda x: x['progress'])[:3],
        'estimated_completion': '2026-03-15',
        'health_status': 'GOOD',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@jarvis_bp.route('/skills', methods=['GET'])
def get_skills():
    """Get skills distribution and status"""
    completed = sum(t['skills'] for t in TEAMS_DATA)

    return jsonify({
        'total_skills': 70,
        'completed': completed,
        'in_progress': 25,
        'pending': 70 - completed - 25,
        'completion_percentage': round(completed / 70 * 100, 1),
        'by_team': [
            {'team_id': t['id'], 'team_name': t['name'], 'skills': t['skills'], 'max_skills': 7}
            for t in TEAMS_DATA
        ],
        'skill_categories': [
            {'category': 'Project Management', 'teams': 3, 'completion': '85%'},
            {'category': 'Software Development', 'teams': 3, 'completion': '62%'},
            {'category': 'Quality Assurance', 'teams': 1, 'completion': '45%'},
            {'category': 'Infrastructure', 'teams': 1, 'completion': '28%'},
            {'category': 'Communication', 'teams': 1, 'completion': '15%'},
            {'category': 'Security', 'teams': 1, 'completion': '35%'}
        ]
    }), 200


@jarvis_bp.route('/health', methods=['GET'])
def health_check():
    """System health status"""
    return jsonify({
        'status': 'operational',
        'uptime': '99.98%',
        'latency': '145ms',
        'error_rate': '0.02%',
        'active_connections': 10,
        'timestamp': datetime.utcnow().isoformat()
    }), 200
