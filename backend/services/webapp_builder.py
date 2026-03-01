"""WebApp Builder Service - Build Your Own Web App in 8 Weeks"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from ..models import db, BootcampEnrollment, WebApp
from ..auth import require_auth, require_subscription
from ..auth import require_auth, require_subscription

webapp_builder_bp = Blueprint('webapp_builder', __name__, url_prefix='/api/webapp-builder')


# Bootcamp Courses
COURSES = {
    'automation_1': {
        'name': '업무 자동화 1: 이메일 + 데이터 입력',
        'duration_weeks': 2,
        'difficulty': 'beginner',
        'description': '반복 업무를 AI로 자동화. 8시간/주'
    },
    'automation_2': {
        'name': '업무 자동화 2: 고객 관리 시스템',
        'duration_weeks': 2,
        'difficulty': 'intermediate',
        'description': '고객 데이터 자동 정리 및 분석'
    },
    'automation_3': {
        'name': '업무 자동화 3: 리포팅 자동화',
        'duration_weeks': 2,
        'difficulty': 'intermediate',
        'description': '일일/주간/월간 리포트 자동 생성'
    },
    'webapp': {
        'name': '나만의 웹앱 만들기',
        'duration_weeks': 2,
        'difficulty': 'advanced',
        'description': 'AI 보조로 풀스택 웹앱 개발. HTML + Python + DB'
    }
}

# Bootcamp Plans
PLANS = {
    'weekday': {
        'name': '평일반 (월~금)',
        'price': 590000,
        'duration': '8주',
        'schedule': '19:00~21:00 (2시간/일, 5일/주)',
        'seats': 3,
        'available': 3
    },
    'weekend': {
        'name': '주말반 (토~일)',
        'price': 590000,
        'duration': '8주',
        'schedule': '10:00~14:00 (4시간/일, 2일/주)',
        'seats': 0,
        'available': 0
    }
}


# Routes

@webapp_builder_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get bootcamp plans"""
    return jsonify(PLANS), 200


@webapp_builder_bp.route('/courses', methods=['GET'])
def get_courses():
    """Get bootcamp courses"""
    return jsonify(COURSES), 200


@webapp_builder_bp.route('/enroll', methods=['POST'])
@require_auth
@require_subscription('webapp-builder')
def enroll_bootcamp():
    """Enroll in bootcamp"""
    data = request.get_json()

    plan_type = data.get('plan_type')  # 'weekday' or 'weekend'

    if plan_type not in PLANS:
        return jsonify({'error': 'Invalid plan type'}), 400

    plan = PLANS[plan_type]
    if plan['available'] <= 0:
        return jsonify({'error': 'No seats available'}), 400

    # Check if already enrolled
    existing = BootcampEnrollment.query.filter_by(
        user_id=g.user_id,
        status='in_progress'
    ).first()

    if existing:
        return jsonify({'error': 'Already enrolled in active bootcamp'}), 400

    # Create enrollment
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(weeks=8)

    enrollment = BootcampEnrollment(
        user_id=g.user_id,
        plan_type=plan_type,
        start_date=start_date,
        end_date=end_date,
        status='in_progress'
    )

    db.session.add(enrollment)
    db.session.commit()

    return jsonify({
        'id': enrollment.id,
        'message': f'Enrolled in {plan["name"]}',
        'enrollment': enrollment.to_dict()
    }), 201


@webapp_builder_bp.route('/enrollments', methods=['GET'])
@require_auth
@require_subscription('webapp-builder')
def get_enrollments():
    """Get user's bootcamp enrollments"""
    enrollments = BootcampEnrollment.query.filter_by(user_id=g.user_id).all()

    return jsonify([e.to_dict() for e in enrollments]), 200


@webapp_builder_bp.route('/webapps', methods=['GET'])
@require_auth
@require_subscription('webapp-builder')
def get_webapps():
    """Get user's created webapps"""
    webapps = WebApp.query.filter_by(user_id=g.user_id).all()

    return jsonify([w.to_dict() for w in webapps]), 200


@webapp_builder_bp.route('/webapps', methods=['POST'])
@require_auth
@require_subscription('webapp-builder')
def create_webapp():
    """Create new webapp project"""
    data = request.get_json()

    required = ['name']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    webapp = WebApp(
        user_id=g.user_id,
        name=data['name'],
        description=data.get('description', ''),
        status='draft'
    )

    db.session.add(webapp)
    db.session.commit()

    return jsonify({
        'id': webapp.id,
        'message': 'WebApp project created',
        'webapp': webapp.to_dict()
    }), 201


@webapp_builder_bp.route('/webapps/<int:webapp_id>', methods=['GET'])
@require_auth
@require_subscription('webapp-builder')
def get_webapp(webapp_id):
    """Get webapp details"""
    webapp = WebApp.query.get(webapp_id)

    if not webapp or webapp.user_id != g.user_id:
        return jsonify({'error': 'WebApp not found'}), 404

    return jsonify(webapp.to_dict()), 200


@webapp_builder_bp.route('/webapps/<int:webapp_id>/deploy', methods=['POST'])
@require_auth
@require_subscription('webapp-builder')
def deploy_webapp(webapp_id):
    """Deploy webapp to live"""
    webapp = WebApp.query.get(webapp_id)

    if not webapp or webapp.user_id != g.user_id:
        return jsonify({'error': 'WebApp not found'}), 404

    data = request.get_json() or {}

    webapp.status = 'deployed'
    webapp.url = data.get('url')
    webapp.code_repo = data.get('repo')
    webapp.deployed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': 'WebApp deployed successfully',
        'webapp': webapp.to_dict()
    }), 200


@webapp_builder_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_subscription('webapp-builder')
def get_dashboard():
    """Get bootcamp dashboard"""
    enrollments = BootcampEnrollment.query.filter_by(user_id=g.user_id).all()
    webapps = WebApp.query.filter_by(user_id=g.user_id).all()

    active_enrollment = next((e for e in enrollments if e.status == 'in_progress'), None)

    return jsonify({
        'active_enrollment': active_enrollment.to_dict() if active_enrollment else None,
        'total_enrollments': len(enrollments),
        'webapps_created': len(webapps),
        'webapps_deployed': len([w for w in webapps if w.status == 'deployed']),
        'courses': COURSES
    }), 200
