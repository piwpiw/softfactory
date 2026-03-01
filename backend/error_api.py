"""Error Tracking API Endpoints

Flask blueprint for error tracking and prevention API.
Provides production-ready error logging, analysis, and prevention features.
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime
from .error_tracker import ErrorTracker
from .auth import require_auth

# Initialize error tracker instance (singleton)
error_tracker = ErrorTracker()

# Create blueprint
error_bp = Blueprint('errors', __name__, url_prefix='/api/errors')


@error_bp.route('/log', methods=['POST'])
def log_error():
    """
    Log a new error with full context.

    Request body:
    {
        "error_type": "ValueError",
        "message": "Invalid input format",
        "traceback": "...",
        "context": {...},
        "project_id": "coocook",
        "user_id": 123,
        "file": "backend/services/coocook.py",
        "line": 45
    }

    Returns:
        JSON with logged error details and pattern detection results
    """
    try:
        data = request.get_json() or {}

        # Validate required fields
        required = ['error_type', 'message', 'traceback']
        if not all(k in data for k in required):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: error_type, message, traceback'
            }), 400

        # Log the error
        result = error_tracker.log_error(
            error_type=data['error_type'],
            message=data['message'],
            traceback=data['traceback'],
            context=data.get('context'),
            project_id=data.get('project_id'),
            user_id=data.get('user_id'),
            file=data.get('file', 'unknown'),
            line=data.get('line', 0)
        )

        return jsonify(result), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error logging failed: {str(e)}'
        }), 500


@error_bp.route('/recent', methods=['GET'])
def get_recent_errors():
    """
    Get recent errors with optional filtering.

    Query parameters:
        - limit: Maximum errors to return (default: 10)
        - project_id: Filter by project ID
        - error_type: Filter by error type
        - offset: Pagination offset (default: 0)

    Returns:
        JSON list of recent errors
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        project_id = request.args.get('project_id')
        error_type = request.args.get('error_type')
        offset = request.args.get('offset', 0, type=int)

        # Validate limits
        limit = min(limit, 100)  # Max 100 per request
        limit = max(limit, 1)    # Min 1 per request

        result = error_tracker.get_recent_errors(
            limit=limit,
            project_id=project_id,
            error_type=error_type,
            offset=offset
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve errors: {str(e)}'
        }), 500


@error_bp.route('/patterns', methods=['GET'])
def get_error_patterns():
    """
    Get detected error patterns.

    Query parameters:
        - error_type: Filter by error type
        - severity: Filter by severity (low, medium, high, critical)

    Returns:
        JSON list of detected patterns with analysis
    """
    try:
        error_type = request.args.get('error_type')
        severity = request.args.get('severity')

        patterns = error_tracker.get_error_patterns(
            error_type=error_type,
            severity=severity
        )

        return jsonify({
            'patterns': patterns,
            'total': len(patterns)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve patterns: {str(e)}'
        }), 500


@error_bp.route('/patterns/<pattern_id>/prevention', methods=['GET'])
def get_pattern_prevention(pattern_id: str):
    """
    Get prevention suggestions for a specific pattern.

    URL parameters:
        - pattern_id: Pattern identifier

    Returns:
        JSON with prevention rules and code examples
    """
    try:
        # Check if pattern exists
        patterns = error_tracker.get_error_patterns()
        pattern = next((p for p in patterns if p['pattern_id'] == pattern_id), None)

        if not pattern:
            return jsonify({
                'success': False,
                'error': f'Pattern {pattern_id} not found'
            }), 404

        # Get prevention suggestions
        error_type = pattern['error_type']
        suggestions = error_tracker.get_prevention_suggestions(error_type)

        return jsonify({
            'pattern_id': pattern_id,
            'suggestions': suggestions
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve prevention suggestions: {str(e)}'
        }), 500


@error_bp.route('/patterns/<pattern_id>/resolve', methods=['POST'])
def resolve_pattern(pattern_id: str):
    """
    Mark an error pattern as resolved.

    Request body:
    {
        "resolution": "Fixed decorator order in auth.py line 45"
    }

    URL parameters:
        - pattern_id: Pattern identifier

    Returns:
        JSON confirming resolution
    """
    try:
        data = request.get_json() or {}

        if 'resolution' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: resolution'
            }), 400

        result = error_tracker.report_pattern_fixed(
            pattern_id=pattern_id,
            resolution=data['resolution']
        )

        if not result['success']:
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to resolve pattern: {str(e)}'
        }), 500


@error_bp.route('/health', methods=['GET'])
def error_health_check():
    """
    Get error tracking system health and statistics.

    Returns:
        JSON with health metrics and critical patterns
    """
    try:
        health = error_tracker.get_health_check()
        status_code = 200 if health['status'] == 'healthy' else 503

        return jsonify(health), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Health check failed: {str(e)}'
        }), 500
