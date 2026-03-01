"""AI Automation Service - Business Automation with AI Employees"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..models import db, AIEmployee, Scenario
from ..auth import require_auth, require_subscription

ai_automation_bp = Blueprint('ai_automation', __name__, url_prefix='/api/ai-automation')


# Service Plans
PLANS = {
    'starter': {
        'name': 'Starter',
        'price': 49000,
        'hours_saved': '10시간',
        'features': ['기본 레슨', '월 2개 시나리오 토큰', '커뮤니티 Q&A']
    },
    'ambassador': {
        'name': 'Ambassador',
        'price': 89000,
        'hours_saved': '15시간',
        'features': ['전체 레슨 + 워크샵', '월 4개 시나리오 토큰', '1:1 코칭', '우선 Q&A', '신규 시나리오 우선']
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 290000,
        'hours_saved': '30시간',
        'features': ['무제한 레슨 + 워크샵', '무제한 시나리오 토큰', '전담 코칭', '우선 지원', '커스텀 시나리오']
    }
}


# Routes

@ai_automation_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get available subscription plans"""
    return jsonify(PLANS), 200


@ai_automation_bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    """Get available automation scenarios"""
    category = request.args.get('category')

    query = Scenario.query
    if category:
        query = query.filter_by(category=category)

    scenarios = query.all()
    return jsonify([s.to_dict() for s in scenarios]), 200


@ai_automation_bp.route('/scenarios/<int:scenario_id>', methods=['GET'])
def get_scenario_detail(scenario_id):
    """Get scenario details"""
    scenario = Scenario.query.get(scenario_id)

    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404

    return jsonify(scenario.to_dict()), 200


@ai_automation_bp.route('/employees', methods=['GET'])
@require_auth
@require_subscription('ai-automation')
def get_ai_employees():
    """Get user's AI employees"""
    employees = AIEmployee.query.filter_by(user_id=g.user_id).all()

    return jsonify([e.to_dict() for e in employees]), 200


@ai_automation_bp.route('/employees', methods=['POST'])
@require_auth
@require_subscription('ai-automation')
def create_ai_employee():
    """Create new AI employee (automation)"""
    data = request.get_json()

    required = ['name', 'scenario_type']
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate scenario type
    valid_types = ['email', 'social', 'customer_service', 'data_entry', 'scheduling']
    if data['scenario_type'] not in valid_types:
        return jsonify({'error': 'Invalid scenario type'}), 400

    employee = AIEmployee(
        user_id=g.user_id,
        name=data['name'],
        scenario_type=data['scenario_type'],
        description=data.get('description', ''),
        status='draft'
    )

    db.session.add(employee)
    db.session.commit()

    return jsonify({
        'id': employee.id,
        'message': 'AI Employee created successfully',
        'employee': employee.to_dict()
    }), 201


@ai_automation_bp.route('/employees/<int:employee_id>', methods=['GET'])
@require_auth
@require_subscription('ai-automation')
def get_ai_employee(employee_id):
    """Get AI employee details"""
    employee = AIEmployee.query.get(employee_id)

    if not employee or employee.user_id != g.user_id:
        return jsonify({'error': 'AI Employee not found'}), 404

    return jsonify(employee.to_dict()), 200


@ai_automation_bp.route('/employees/<int:employee_id>/deploy', methods=['POST'])
@require_auth
@require_subscription('ai-automation')
def deploy_ai_employee(employee_id):
    """Deploy AI employee (activate)"""
    employee = AIEmployee.query.get(employee_id)

    if not employee or employee.user_id != g.user_id:
        return jsonify({'error': 'AI Employee not found'}), 404

    data = request.get_json() or {}

    # Set deployment parameters
    employee.status = 'training'  # 일반적으로 training → active 순서
    employee.monthly_savings_hours = data.get('savings_hours', 10)
    employee.deployed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'id': employee.id,
        'message': 'AI Employee deployed successfully',
        'status': employee.status
    }), 200


@ai_automation_bp.route('/employees/<int:employee_id>/activate', methods=['POST'])
@require_auth
@require_subscription('ai-automation')
def activate_ai_employee(employee_id):
    """Activate AI employee (move from training to active)"""
    employee = AIEmployee.query.get(employee_id)

    if not employee or employee.user_id != g.user_id:
        return jsonify({'error': 'AI Employee not found'}), 404

    employee.status = 'active'
    db.session.commit()

    return jsonify({
        'message': 'AI Employee activated successfully',
        'status': 'active'
    }), 200


@ai_automation_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@require_auth
@require_subscription('ai-automation')
def delete_ai_employee(employee_id):
    """Delete AI employee"""
    employee = AIEmployee.query.get(employee_id)

    if not employee or employee.user_id != g.user_id:
        return jsonify({'error': 'AI Employee not found'}), 404

    if employee.status == 'active':
        return jsonify({'error': 'Cannot delete active AI Employee. Pause first.'}), 400

    db.session.delete(employee)
    db.session.commit()

    return jsonify({'message': 'AI Employee deleted'}), 200


@ai_automation_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_subscription('ai-automation')
def get_dashboard():
    """Get automation dashboard summary"""
    employees = AIEmployee.query.filter_by(user_id=g.user_id).all()

    active_count = len([e for e in employees if e.status == 'active'])
    total_savings = sum(e.monthly_savings_hours or 0 for e in employees)

    return jsonify({
        'total_employees': len(employees),
        'active_employees': active_count,
        'total_monthly_savings_hours': total_savings,
        'estimated_annual_savings': f'₩{total_savings * 15000:,}',  # 시간당 15000원 기준
        'employees': [e.to_dict() for e in employees]
    }), 200
