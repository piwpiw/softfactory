"""Scheduler Status & Control API — Endpoints for monitoring and managing background jobs.

Blueprint prefix: /api/scheduler

Endpoints:
    GET  /api/scheduler/status              — All jobs and their next run times
    POST /api/scheduler/trigger/<job_id>    — Manually trigger a job
    GET  /api/scheduler/history             — Recent job execution history
    PUT  /api/scheduler/job/<job_id>/toggle — Enable/disable a job
    GET  /api/scheduler/data/stats          — Accumulated data statistics
    GET  /api/scheduler/data/freshness      — Data freshness per platform
    GET  /api/scheduler/data/crawl-history  — Crawl log history
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger('scheduler_routes')

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')


# ---------------------------------------------------------------------------
# GET /api/scheduler/status
# ---------------------------------------------------------------------------

@scheduler_bp.route('/status', methods=['GET'])
def scheduler_status():
    """Return all registered jobs, their next run times, and scheduler state."""
    from backend.scheduler import get_scheduler_status
    return jsonify(get_scheduler_status()), 200


# ---------------------------------------------------------------------------
# POST /api/scheduler/trigger/<job_id>
# ---------------------------------------------------------------------------

@scheduler_bp.route('/trigger/<job_id>', methods=['POST'])
def trigger_job(job_id):
    """Manually trigger a specific job by its ID.

    The job will run at the next scheduler tick (almost immediately).
    """
    from backend.scheduler import trigger_job as _trigger

    found = _trigger(job_id)
    if not found:
        return jsonify({'error': f'Job "{job_id}" not found'}), 404

    logger.info(f'[SCHEDULER-API] Manually triggered job: {job_id}')
    return jsonify({
        'message': f'Job "{job_id}" triggered successfully',
        'job_id': job_id,
    }), 200


# ---------------------------------------------------------------------------
# GET /api/scheduler/history
# ---------------------------------------------------------------------------

@scheduler_bp.route('/history', methods=['GET'])
def job_history():
    """Return recent job execution history.

    Query params:
        limit (int, default 50) — max entries to return
    """
    from backend.scheduler import get_job_history

    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 500)
    history = get_job_history(limit=limit)
    return jsonify({
        'entries': history,
        'count': len(history),
    }), 200


# ---------------------------------------------------------------------------
# PUT /api/scheduler/job/<job_id>/toggle
# ---------------------------------------------------------------------------

@scheduler_bp.route('/job/<job_id>/toggle', methods=['PUT'])
def toggle_job(job_id):
    """Pause or resume a scheduled job.

    If the job is active it will be paused; if paused it will be resumed.
    """
    from backend.scheduler import toggle_job as _toggle

    result = _toggle(job_id)
    if result is None:
        return jsonify({'error': f'Job "{job_id}" not found'}), 404

    logger.info(f'[SCHEDULER-API] Toggled job {job_id} -> {result["state"]}')
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# GET /api/scheduler/data/stats — Accumulated data statistics
# ---------------------------------------------------------------------------

@scheduler_bp.route('/data/stats', methods=['GET'])
def data_stats():
    """Return accumulated crawl data statistics (totals, by platform, by date)."""
    from backend.data_accumulator import get_accumulated_stats
    stats = get_accumulated_stats()
    return jsonify(stats), 200


# ---------------------------------------------------------------------------
# GET /api/scheduler/data/freshness — Data freshness per platform
# ---------------------------------------------------------------------------

@scheduler_bp.route('/data/freshness', methods=['GET'])
def data_freshness():
    """Return how old the crawled data is per platform."""
    from backend.data_accumulator import get_data_freshness
    freshness = get_data_freshness()
    return jsonify(freshness), 200


# ---------------------------------------------------------------------------
# GET /api/scheduler/data/crawl-history — Crawl log history
# ---------------------------------------------------------------------------

@scheduler_bp.route('/data/crawl-history', methods=['GET'])
def crawl_history():
    """Return CrawlerLog entries.

    Query params:
        platform (str, optional) — filter by platform
        days (int, default 30) — how many days back
    """
    from backend.data_accumulator import get_crawl_history

    platform = request.args.get('platform')
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)

    history = get_crawl_history(platform=platform, days=days)
    return jsonify({
        'entries': history,
        'count': len(history),
        'platform_filter': platform,
        'days': days,
    }), 200
