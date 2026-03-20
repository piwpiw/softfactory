"""SoftFactory Flask Application - Security-Hardened + Production Monitoring"""
from flask import Flask, jsonify, send_from_directory, request, redirect, g, abort
from flask_cors import CORS
from flask_migrate import Migrate
import os
import time
import threading
import collections
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text as sa_text
from .models import db, init_db
from .auth import auth_bp
from .websocket_server import init_websocket
from .payment import payment_bp
from .platform_routes import platform_bp
from .services.file_service import file_bp
from .services.coocook import coocook_bp
from .services.sns_auto import sns_bp
from .services.instagram_api import instagram_bp
from .services.sns_revenue_api import sns_revenue_bp
from .services.twitter_routes import twitter_bp
from .services.review import review_bp
from .services.ai_automation import ai_automation_bp
from .services.instagram_cardnews import instagram_cardnews_bp
from .services.webapp_builder import webapp_builder_bp
from .services.dashboard import dashboard_bp
from .services.analytics import analytics_bp
from .services.performance import performance_bp
from .services.settings import settings_bp
from .services.claude_ai_routes import claude_ai_bp
from .services.scheduler_routes import scheduler_bp
from .services.encryption_api import encryption_bp
from .services.nutrition_bp import nutrition_bp
from .services.shopping_list import shopping_bp
from .services.feed import feed_bp
from .services.telegram_routes import telegram_bp
from .services.notifications import notifications_bp
from .services.rbac_routes import rbac_bp
from .rbac import init_rbac
from .services.search_routes import search_bp
from .services.video_processor import video_bp
from .services.admin_routes import admin_bp
from .services.bohemian_marketing import bohemian_marketing_bp
from .services.growth_automation import growth_automation_bp
from .services.event_gateway import event_gateway_bp
from .services.wordpress_publisher_service import wordpress_bp
from .metrics import metrics_bp, register_metrics_middleware
from . import oauth
from .logging_config import configure_logging, request_logging_middleware
from .config import Config
from .config_validator import validate_config
from .auth import require_auth, require_admin
from .error_api import error_bp
from .runtime_paths import default_app_log_path


# Allowed CORS origins ??restrict to known frontends only
ALLOWED_ORIGINS = [
    "http://localhost:5000",
    "http://localhost:8000",
    "http://localhost:9000",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:9000",
]

# Add production domain from environment if configured
_PRODUCTION_ORIGIN = os.getenv('CORS_ALLOWED_ORIGIN')
if _PRODUCTION_ORIGIN:
    ALLOWED_ORIGINS.append(_PRODUCTION_ORIGIN)
    ALLOWED_ORIGINS.append(_PRODUCTION_ORIGIN.rstrip('/'))

# Add Vercel deployment hostname if available
_VERCEL_ORIGIN = os.getenv('VERCEL_URL')
if _VERCEL_ORIGIN:
    if '://' not in _VERCEL_ORIGIN:
        ALLOWED_ORIGINS.append(f'https://{_VERCEL_ORIGIN}')
    else:
        ALLOWED_ORIGINS.append(_VERCEL_ORIGIN)

# Add extra comma-separated origins if needed (production override)
_EXTRA_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '')
if _EXTRA_ORIGINS:
    for _origin in [item.strip() for item in _EXTRA_ORIGINS.split(',')]:
        if _origin:
            ALLOWED_ORIGINS.append(_origin)

ALLOWED_ORIGINS = sorted({origin.rstrip('/') for origin in ALLOWED_ORIGINS})


# ---------------------------------------------------------------------------
# In-memory request telemetry store (thread-safe, minimal overhead)
# ---------------------------------------------------------------------------

_METRICS_LOCK = threading.Lock()

# Per-endpoint counters: { "METHOD /path" -> {count, errors, total_ms, slow} }
_endpoint_stats: dict = collections.defaultdict(lambda: {
    'count': 0, 'errors': 0, 'total_ms': 0.0, 'slow': 0
})

_total_requests: int = 0
_total_errors: int   = 0

# Bounded deque of recent 5xx timestamps for sliding-window alert check
_error_timestamps: collections.deque = collections.deque(maxlen=10_000)

# Last 10 error details surfaced via /api/admin/metrics
_recent_errors: collections.deque = collections.deque(maxlen=10)

# Alert cooldown ??prevent spam (2 min between identical alerts)
_last_high_error_rate_alert: float = 0.0
_ALERT_COOLDOWN_SECONDS: int = 120


def _record_request(endpoint: str, method: str, status_code: int,
                    duration_ms: float) -> None:
    """Update in-memory telemetry counters.  Must complete in < 1 ms."""
    global _total_requests, _total_errors
    key = f'{method} {endpoint}'
    is_5xx = status_code >= 500

    with _METRICS_LOCK:
        _total_requests += 1
        _endpoint_stats[key]['count']    += 1
        _endpoint_stats[key]['total_ms'] += duration_ms
        if is_5xx:
            _total_errors += 1
            _endpoint_stats[key]['errors'] += 1
            _error_timestamps.append(time.time())
            _recent_errors.append({
                'endpoint':    endpoint,
                'method':      method,
                'status_code': status_code,
                'duration_ms': round(duration_ms, 1),
                'timestamp':   datetime.now(timezone.utc).isoformat(),
            })
        if duration_ms > 1000:
            _endpoint_stats[key]['slow'] += 1


def _error_count_in_window(window_seconds: int = 60) -> int:
    """Return number of 5xx responses in the last ``window_seconds``."""
    cutoff = time.time() - window_seconds
    with _METRICS_LOCK:
        return sum(1 for ts in _error_timestamps if ts >= cutoff)


def _maybe_alert_high_error_rate(app) -> None:
    """Send Telegram alert if 5xx rate > 10 % in last 60 s (with cooldown)."""
    global _last_high_error_rate_alert
    try:
        errors = _error_count_in_window(60)
        total  = max(_total_requests, 1)
        if errors / total < 0.10:
            return
        now = time.time()
        if now - _last_high_error_rate_alert < _ALERT_COOLDOWN_SECONDS:
            return
        _last_high_error_rate_alert = now
        from .services.alert_service import alert_service
        alert_service.alert_high_error_rate(errors, 60)
    except Exception:
        pass  # Never let alerting affect a request


def create_app():
    """Application factory"""
    app = Flask(__name__)
    log_file = os.getenv('LOG_FILE') or str(default_app_log_path())
    configure_logging(
        app,
        log_file=log_file,
        debug=str(os.getenv('FLASK_ENV', '')).lower() == 'development'
    )
    request_logging_middleware(app)

    # Record start time for uptime calculation (also used by /health and /metrics)
    app._start_time = time.time()
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('ENVIRONMENT', '').strip().lower() == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Configuration ??environment-based database URL
    # Use DATABASE_URL env var if set (PostgreSQL production), otherwise fall back to SQLite (dev)
    db_url = os.getenv('DATABASE_URL')
    if db_url and '<' in db_url:
        db_url = ''
    if not db_url:
        # SQLite development default ??absolute path prevents duplicate DB creation
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'platform.db')
        db_url = f'sqlite:///{db_path}'
    elif db_url.startswith('postgres://'):
        # Heroku / Railway legacy scheme ??SQLAlchemy-compatible scheme
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    # Enforce strict runtime DB validation for production.
    is_production = os.getenv('ENVIRONMENT', '').strip().lower() == 'production'
    _runtime_db_url = Config.get_database_url()
    if _runtime_db_url:
        if not Config.is_database_url_safe(_runtime_db_url):
            raise RuntimeError('DATABASE_URL is invalid or uses unsupported format.')
        if is_production and _runtime_db_url.startswith('sqlite'):
            raise RuntimeError('DATABASE_URL must not use sqlite in production.')
        db_url = _runtime_db_url
    elif is_production:
        raise RuntimeError('DATABASE_URL is required and must be valid in production mode.')

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['TESTING'] = os.getenv('TESTING', '').strip().lower() in {'1', 'true', 'yes', 'on'}

    # Database connection pool optimization
    # SQLite uses StaticPool (single connection) by default -- pool_size is N/A
    # These settings activate automatically when DATABASE_URL is PostgreSQL/MySQL
    if db_url.startswith('sqlite'):
        # SQLite optimizations: WAL mode for concurrent reads, increase cache
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,   # Verify connection liveness before checkout
            'connect_args': {
                'check_same_thread': False,  # Allow multi-threaded access
            },
        }
    else:
        # PostgreSQL connection pool tuning for production workloads
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,          # Max persistent connections in the pool
            'pool_recycle': 1800,     # Recycle connections after 30 minutes
            'pool_pre_ping': True,    # Verify connection liveness before checkout
            'max_overflow': 20,       # Allow up to 20 additional connections beyond pool_size
            'pool_timeout': 30,       # Wait up to 30s for a connection from the pool
        }

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)  # noqa: F841 ??registers flask db CLI commands

    # Initialise Sentry error tracking (silent no-op when SENTRY_DSN absent)
    from .monitoring import init_sentry
    init_sentry(app)

    # CORS ??Hardened configuration
    # Removed "null" origin (security risk: allows file:// protocol abuse)
    # Restricted to known origins, methods, and headers only
    CORS(app, resources={r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
        "supports_credentials": True,
        "max_age": 600,  # Cache preflight for 10 minutes
    }})

    # Inject OAuth configuration from Config class
    oauth.OAUTH_PROVIDERS['google']['client_id'] = Config.GOOGLE_CLIENT_ID
    oauth.OAUTH_PROVIDERS['google']['client_secret'] = Config.GOOGLE_CLIENT_SECRET
    oauth.OAUTH_PROVIDERS['facebook']['client_id'] = Config.FACEBOOK_APP_ID
    oauth.OAUTH_PROVIDERS['facebook']['client_secret'] = Config.FACEBOOK_APP_SECRET
    oauth.OAUTH_PROVIDERS['kakao']['client_id'] = Config.KAKAO_REST_API_KEY
    oauth.OAUTH_PROVIDERS['kakao']['client_secret'] = Config.KAKAO_CLIENT_SECRET

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(coocook_bp)
    app.register_blueprint(sns_bp)
    app.register_blueprint(instagram_bp)
    app.register_blueprint(sns_revenue_bp)
    app.register_blueprint(twitter_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(ai_automation_bp)
    app.register_blueprint(instagram_cardnews_bp)
    app.register_blueprint(webapp_builder_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(claude_ai_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(encryption_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(telegram_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(rbac_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(bohemian_marketing_bp)
    app.register_blueprint(growth_automation_bp)
    app.register_blueprint(event_gateway_bp)
    app.register_blueprint(wordpress_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(error_bp)
    register_metrics_middleware(app)

    # Initialize Elasticsearch service
    from .services.elasticsearch_service import init_elasticsearch
    from .services.search_admin import register_search_admin
    init_elasticsearch(app)
    register_search_admin(app)

    # Register cache stats endpoint
    from .cache import get_cache
    @app.route('/api/perf/cache-stats')
    def cache_stats():
        return jsonify(get_cache().stats()), 200

    # -----------------------------------------------------------------------
    # Request tracking middleware  (Task 5)
    # -----------------------------------------------------------------------

    @app.before_request
    def _before_request_tracking():
        """Stamp high-resolution start time onto the request context."""
        g._req_start = time.perf_counter()

    @app.after_request
    def _after_request_tracking(response):
        """Collect telemetry and fire slow/error alerts for every response.

        All operations are in-memory (no I/O), so overhead is negligible.
        Any exception is swallowed to guarantee responses are never blocked.
        """
        try:
            start = getattr(g, '_req_start', None)
            duration_ms = (time.perf_counter() - start) * 1000 if start is not None else 0.0
            endpoint    = request.endpoint or request.path
            method      = request.method
            status      = response.status_code

            _record_request(endpoint, method, status, duration_ms)

            if duration_ms > 1000:
                app.logger.warning(
                    f'Slow request: {method} {request.path} '
                    f'??{duration_ms:.0f} ms (HTTP {status})'
                )

            if status >= 500:
                _maybe_alert_high_error_rate(app)

        except Exception:
            pass  # Telemetry errors must never affect the response

        return response

    # -----------------------------------------------------------------------
    # Health check ??comprehensive (Task 2)
    # -----------------------------------------------------------------------
    @app.route('/ready')
    def readiness_alias():
        """Container/Kubernetes compatibility alias for readiness."""
        try:
            db.session.execute(sa_text('SELECT 1'))
            return jsonify({
                'ready': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': os.getenv('APP_VERSION', '1.0.0')
            }), 200
        except Exception:
            return jsonify({
                'ready': False,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': os.getenv('APP_VERSION', '1.0.0'),
                'reason': 'database unavailable'
            }), 503

    @app.route('/health')
    def health():
        """Comprehensive health check: DB, scheduler, AI service, memory, uptime."""
        import psutil

        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        status = {
            'status':    'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version':   os.getenv('APP_VERSION', '1.0.0'),
            'database_backend': Config.get_database_backend(db_uri),
        }

        # Uptime
        elapsed = time.time() - app._start_time
        hours, rem = divmod(int(elapsed), 3600)
        mins, secs = divmod(rem, 60)
        status['uptime']         = f'{hours}h {mins}m {secs}s'
        status['uptime_seconds'] = int(elapsed)

        # Database
        try:
            db.session.execute(sa_text('SELECT 1'))
            status['database'] = 'connected'
        except Exception as exc:
            status['database'] = 'disconnected'
            status['status']   = 'degraded'
            app.logger.error(f'Health ??DB error: {exc}')
            try:
                from .services.alert_service import alert_service
                alert_service.alert_db_connection_failed()
            except Exception:
                pass

        # Scheduler
        try:
            from .scheduler import get_scheduler_status
            sched = get_scheduler_status()
            status['scheduler']      = 'running' if sched.get('running') else 'stopped'
            status['scheduler_jobs'] = sched.get('job_count', 0)
        except Exception:
            status['scheduler'] = 'unavailable'

        # AI service
        try:
            from .services.claude_ai import claude_ai
            status['ai_service'] = 'available' if claude_ai.is_available() else 'unavailable'
        except Exception:
            status['ai_service'] = 'unknown'

        # Service blueprint availability
        bp_map = {
            'sns_auto':       'sns',
            'review':         'review',
            'coocook':        'coocook',
            'ai_automation':  'ai_automation',
            'webapp_builder': 'webapp_builder',
            'claude_ai':      'claude_ai',
        }
        services = {}
        for key, bp_name in bp_map.items():
            if bp_name in app.blueprints:
                services[key] = 'ok'
            else:
                services[key] = 'unavailable'
                status['status'] = 'degraded'
        status['services'] = services

        # Memory & CPU
        try:
            proc = psutil.Process()
            status['memory_mb']   = round(proc.memory_info().rss / 1024 / 1024, 1)
            status['cpu_percent'] = proc.cpu_percent()
        except Exception:
            pass

        http_code = 200 if status['status'] == 'ok' else 503
        return jsonify(status), http_code

    @app.route('/api/health')
    def api_health():
        """Compatibility health check endpoint (legacy path)."""
        return health()

    # -----------------------------------------------------------------------
    # Prometheus-compatible /metrics endpoint  (Task 3)
    # -----------------------------------------------------------------------

    @app.route('/metrics')
    def prometheus_metrics():
        """Prometheus plaintext metrics.

        Exported metrics:
          http_requests_total{endpoint,method,status}
          http_request_duration_seconds{endpoint,method}   (average)
          http_slow_requests_total{endpoint,method}
          active_users_gauge
          scheduled_jobs_gauge
          app_uptime_seconds
          process_memory_mb
          process_cpu_percent
        """
        import psutil

        lines = []

        def _emit(name, help_text, mtype, samples):
            lines.append(f'# HELP {name} {help_text}')
            lines.append(f'# TYPE {name} {mtype}')
            for labels, value in samples:
                if labels:
                    lstr = ','.join(f'{k}="{v}"' for k, v in labels.items())
                    lines.append(f'{name}{{{lstr}}} {value}')
                else:
                    lines.append(f'{name} {value}')
            lines.append('')

        with _METRICS_LOCK:
            snap = dict(_endpoint_stats)

        req_samples  = []
        dur_samples  = []
        slow_samples = []

        for key, s in snap.items():
            method, _, endpoint = key.partition(' ')
            count = s['count']
            if count == 0:
                continue
            errors = s['errors']
            req_samples.append(
                ({'endpoint': endpoint, 'method': method, 'status': 'success'}, count - errors)
            )
            if errors:
                req_samples.append(
                    ({'endpoint': endpoint, 'method': method, 'status': 'error'}, errors)
                )
            avg_s = round(s['total_ms'] / count / 1000, 4)
            dur_samples.append(({'endpoint': endpoint, 'method': method}, avg_s))
            if s['slow']:
                slow_samples.append(({'endpoint': endpoint, 'method': method}, s['slow']))

        _emit('http_requests_total',
              'Total HTTP requests by endpoint, method, and outcome',
              'counter', req_samples)
        _emit('http_request_duration_seconds',
              'Average HTTP response time in seconds',
              'gauge', dur_samples)
        _emit('http_slow_requests_total',
              'Requests that exceeded the 1 000 ms SLA',
              'counter', slow_samples)

        try:
            from .models import User
            active = User.query.filter_by(is_active=True).count()
        except Exception:
            active = 0
        _emit('active_users_gauge', 'Active user accounts', 'gauge', [(None, active)])

        try:
            from .scheduler import get_scheduler_status
            job_count = get_scheduler_status().get('job_count', 0)
        except Exception:
            job_count = 0
        _emit('scheduled_jobs_gauge', 'Number of scheduled background jobs', 'gauge',
              [(None, job_count)])

        _emit('app_uptime_seconds', 'Application uptime in seconds', 'gauge',
              [(None, int(time.time() - app._start_time))])

        try:
            proc = psutil.Process()
            _emit('process_memory_mb', 'Process RSS memory in MB', 'gauge',
                  [(None, round(proc.memory_info().rss / 1024 / 1024, 1))])
            _emit('process_cpu_percent', 'Process CPU usage %', 'gauge',
                  [(None, proc.cpu_percent())])
        except Exception:
            pass

        return '\n'.join(lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}

    # -----------------------------------------------------------------------
    # Admin metrics endpoint  (Task 6)
    # -----------------------------------------------------------------------

    @app.route('/api/admin/metrics')
    @require_auth
    @require_admin
    def admin_metrics():
        """Protected admin metrics: business KPIs + request telemetry + errors.

        Requires: Authorization: Bearer <admin JWT>

        Returns JSON with:
          - total_users, active_subscriptions, total_revenue
          - global request / error counts + error rate
          - top 5 slowest endpoints
          - top 5 highest error-rate endpoints
          - last 10 errors
          - scheduler status
          - system memory / CPU
        """
        import psutil
        from sqlalchemy import func as sqlfunc

        result = {
            'timestamp':      datetime.now(timezone.utc).isoformat(),
            'version':        os.getenv('APP_VERSION', '1.0.0'),
            'uptime_seconds': int(time.time() - app._start_time),
        }

        # Business metrics
        try:
            from .models import User, Subscription, Payment
            result['total_users']          = User.query.count()
            result['active_subscriptions'] = Subscription.query.filter_by(status='active').count()
            rev = db.session.query(
                sqlfunc.coalesce(sqlfunc.sum(Payment.amount), 0)
            ).scalar()
            result['total_revenue'] = int(rev or 0)
        except Exception as exc:
            app.logger.warning(f'admin_metrics business query failed: {exc}')
            result['total_users']          = None
            result['active_subscriptions'] = None
            result['total_revenue']        = None

        # Request telemetry snapshot
        with _METRICS_LOCK:
            snap         = dict(_endpoint_stats)
            recent_errs  = list(_recent_errors)
            glob_total   = _total_requests
            glob_errors  = _total_errors

        result['global_request_count']   = glob_total
        result['global_error_count']     = glob_errors
        result['global_error_rate_pct']  = round(
            glob_errors / max(glob_total, 1) * 100, 2
        )

        rows = []
        for key, s in snap.items():
            count = s['count']
            if count == 0:
                continue
            method, _, endpoint = key.partition(' ')
            rows.append({
                'endpoint':       endpoint,
                'method':         method,
                'request_count':  count,
                'error_count':    s['errors'],
                'error_rate_pct': round(s['errors'] / count * 100, 1),
                'avg_ms':         round(s['total_ms'] / count, 1),
                'slow_count':     s['slow'],
            })

        result['slowest_endpoints'] = sorted(
            rows, key=lambda r: r['avg_ms'], reverse=True
        )[:5]
        result['error_endpoints'] = sorted(
            [r for r in rows if r['error_count'] > 0],
            key=lambda r: r['error_rate_pct'], reverse=True
        )[:5]
        result['recent_errors'] = recent_errs

        # Scheduler
        try:
            from .scheduler import get_scheduler_status
            result['scheduler'] = get_scheduler_status()
        except Exception:
            result['scheduler'] = {'status': 'unavailable'}

        # System resources
        try:
            proc = psutil.Process()
            result['system'] = {
                'memory_mb':   round(proc.memory_info().rss / 1024 / 1024, 1),
                'cpu_percent': proc.cpu_percent(),
            }
        except Exception:
            result['system'] = {}

        return jsonify(result), 200

    # Serve static files
    web_dir = Path(__file__).parent.parent / 'web'

    @app.route('/')
    def serve_root():
        return redirect('/web/index.html')

    @app.route('/favicon.ico')
    def serve_favicon():
        """Avoid noisy favicon errors when a page does not declare an icon."""
        return '', 204

    @app.route('/web/<path:path>')
    def serve_web(path):
        """Serve web files from /web directory"""
        file_path = web_dir / path
        if file_path.is_file():
            return send_from_directory(web_dir, path)
        # Try to serve directory index.html
        index_file = file_path / 'index.html'
        if index_file.is_file():
            return send_from_directory(file_path, 'index.html')
        return jsonify({'error': 'Not found'}), 404

    @app.route('/web/')
    def serve_web_root():
        """Backward compatibility for /web/ with explicit index."""
        return send_from_directory(web_dir, 'index.html')

    @app.route('/api/status')
    def serve_api_status():
        """Compatibility route for clients expecting /api/status."""
        try:
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'database': 'connected',
                'version': os.getenv('APP_VERSION', '1.0.0')
            }), 200
        except Exception:
            return jsonify({'status': 'error'}), 500

    def _v1_default_teams():
        now_iso = datetime.now(timezone.utc).isoformat()
        return [
            {
                'id': 'team-alpha',
                'name': 'Alpha',
                'members': 12,
                'utilization': 84,
                'throughput': 102,
                'quality': 94,
                'readiness': 88,
                'risk': 2.1,
                'status': 'active',
                'current_task': '플랫폼 성능 최적화',
                'updatedAt': now_iso,
            },
            {
                'id': 'team-beta',
                'name': 'Beta',
                'members': 10,
                'utilization': 76,
                'throughput': 91,
                'quality': 90,
                'readiness': 83,
                'risk': 3.2,
                'status': 'active',
                'current_task': '신규 기능 통합 테스트',
                'updatedAt': now_iso,
            },
            {
                'id': 'team-gamma',
                'name': 'Gamma',
                'members': 8,
                'utilization': 69,
                'throughput': 79,
                'quality': 88,
                'readiness': 80,
                'risk': 4.7,
                'status': 'warn',
                'current_task': '운영 이슈 회귀 점검',
                'updatedAt': now_iso,
            },
            {
                'id': 'team-delta',
                'name': 'Delta',
                'members': 7,
                'utilization': 63,
                'throughput': 70,
                'quality': 86,
                'readiness': 75,
                'risk': 5.1,
                'status': 'warn',
                'current_task': 'UI 일관성 개선',
                'updatedAt': now_iso,
            },
            {
                'id': 'team-omega',
                'name': 'Omega',
                'members': 6,
                'utilization': 58,
                'throughput': 62,
                'quality': 85,
                'readiness': 71,
                'risk': 5.9,
                'status': 'active',
                'current_task': '배포 자동화 정비',
                'updatedAt': now_iso,
            },
        ]

    def _v1_cycles_store():
        rows = app.config.setdefault('V1_AUTOMATION_CYCLES', [])
        if rows:
            return rows

        now_iso = datetime.now(timezone.utc).isoformat()
        rows.extend([
            {
                'id': 'cycle-1003',
                'timestamp': now_iso,
                'iteration': 3,
                'departments': 5,
                'tasks': 18,
                'validation_status': 'ok',
                'failed_departments_in_runner': 0,
                'retry_summary': {
                    'retried': 1,
                    'remaining_failed': 0,
                    'retried_run_results': ['qa-recheck:success'],
                },
                'team_name': 'Alpha',
                'team': 'Alpha',
                'name': 'Alpha Sprint',
                'status': 'active',
                'completion': 72,
                'due': now_iso,
                'goals': '성능, 품질, 배포 안정성 개선',
                'createdAt': now_iso,
            },
            {
                'id': 'cycle-1002',
                'timestamp': now_iso,
                'iteration': 2,
                'departments': 5,
                'tasks': 16,
                'validation_status': 'warn',
                'failed_departments_in_runner': 1,
                'retry_summary': {
                    'retried': 2,
                    'remaining_failed': 1,
                    'retried_run_results': ['ui-regression:success', 'ops-smoke:failed'],
                },
                'team_name': 'Beta',
                'team': 'Beta',
                'name': 'Beta Sprint',
                'status': 'planned',
                'completion': 28,
                'due': now_iso,
                'goals': '운영 대시보드 고도화',
                'createdAt': now_iso,
            },
            {
                'id': 'cycle-1001',
                'timestamp': now_iso,
                'iteration': 1,
                'departments': 4,
                'tasks': 14,
                'validation_status': 'ok',
                'failed_departments_in_runner': 0,
                'retry_summary': {
                    'retried': 0,
                    'remaining_failed': 0,
                    'retried_run_results': [],
                },
                'team_name': 'Gamma',
                'team': 'Gamma',
                'name': 'Gamma Sprint',
                'status': 'done',
                'completion': 100,
                'due': now_iso,
                'goals': '기능 정합성 점검 완료',
                'createdAt': now_iso,
            },
        ])
        return rows

    @app.route('/api/v1/status')
    def serve_api_v1_status():
        """Legacy compatibility status endpoint for static dashboard pages."""
        try:
            uptime_seconds = max(int(time.time() - app._start_time), 0)
            return jsonify({
                'status': 'ok',
                'uptime': 99.95,
                'uptime_seconds': uptime_seconds,
                'latency_ms': 72,
                'error_rate': 0.12,
                'active_sessions': 24,
                'database': 'connected',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': os.getenv('APP_VERSION', '1.0.0'),
            }), 200
        except Exception:
            return jsonify({'status': 'error'}), 500

    @app.route('/api/v1/teams')
    def serve_api_v1_teams():
        """Legacy compatibility endpoint used by root-level dashboard pages."""
        try:
            return jsonify(_v1_default_teams()), 200
        except Exception:
            return jsonify([]), 500

    @app.route('/api/v1/automation/status')
    def serve_api_v1_automation_status():
        """Compatibility endpoint for CI/CD and automation dashboard pages."""
        try:
            cycles = _v1_cycles_store()
            pipelines = [
                {
                    'id': 'p-2003',
                    'version': 'v1.2.34',
                    'branch': 'main',
                    'status': 'success',
                    'started_at': datetime.now(timezone.utc).isoformat(),
                    'message': 'production deploy complete',
                    'build': 'success',
                    'test': 'success',
                    'deploy': 'success',
                    'prod': 'success',
                },
                {
                    'id': 'p-2002',
                    'version': 'v1.2.35',
                    'branch': 'release',
                    'status': 'running',
                    'started_at': datetime.now(timezone.utc).isoformat(),
                    'message': 'integration test running',
                    'build': 'success',
                    'test': 'running',
                    'deploy': 'wait',
                    'prod': 'wait',
                },
                {
                    'id': 'p-2001',
                    'version': 'v1.2.33',
                    'branch': 'main',
                    'status': 'fail',
                    'started_at': datetime.now(timezone.utc).isoformat(),
                    'message': 'deployment rollback applied',
                    'build': 'success',
                    'test': 'success',
                    'deploy': 'fail',
                    'prod': 'stopped',
                },
            ]

            failed_cycle_count = sum(
                1 for row in cycles
                if str(row.get('validation_status', '')).lower() not in ('ok', 'success')
            )
            latest = cycles[0] if cycles else {}
            return jsonify({
                'available': True,
                'status': {
                    'running': any(p.get('status') == 'running' for p in pipelines),
                    'iterations_completed': len(cycles),
                    'iterations_planned': max(len(cycles) + 2, 6),
                    'note': 'compatibility mode',
                    'last_updated': latest.get('timestamp') or datetime.now(timezone.utc).isoformat(),
                },
                'total_alerts': failed_cycle_count,
                'total_pipelines': len(pipelines),
                'pipelines': pipelines,
            }), 200
        except Exception:
            return jsonify({'available': False}), 500

    @app.route('/api/v1/automation/hourly')
    def serve_api_v1_automation_hourly():
        """Compatibility hourly automation report summary."""
        try:
            cycles = _v1_cycles_store()
            latest = cycles[0] if cycles else {}
            return jsonify({
                'available': True,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'latest_cycle': latest,
                'summary': {
                    'cycles': len(cycles),
                    'open_issues': sum(
                        1 for row in cycles
                        if str(row.get('validation_status', '')).lower() not in ('ok', 'success')
                    ),
                },
            }), 200
        except Exception:
            return jsonify({'available': False}), 500

    @app.route('/api/v1/automation/cycles', methods=['GET', 'POST'])
    def serve_api_v1_automation_cycles():
        """Compatibility endpoint for sprint/CI pages requiring cycle history."""
        try:
            rows = _v1_cycles_store()

            if request.method == 'POST':
                payload = request.get_json(silent=True) or {}
                now_iso = datetime.now(timezone.utc).isoformat()
                next_iteration = len(rows) + 1
                status_text = str(payload.get('status') or 'active')
                validation_status = str(
                    payload.get('validation_status')
                    or ('ok' if status_text in ('active', 'done', 'success') else 'warn')
                )
                failed_count = payload.get('failed_departments_in_runner')
                if failed_count is None:
                    failed_count = 0 if validation_status in ('ok', 'success') else 1

                new_row = {
                    'id': payload.get('id') or f'cycle-{int(time.time())}',
                    'timestamp': now_iso,
                    'iteration': next_iteration,
                    'departments': int(payload.get('departments') or 5),
                    'tasks': int(payload.get('tasks') or 12),
                    'validation_status': validation_status,
                    'failed_departments_in_runner': int(failed_count),
                    'retry_summary': {
                        'retried': 0,
                        'remaining_failed': int(failed_count),
                        'retried_run_results': [],
                    },
                    'team_name': str(payload.get('team') or 'Alpha'),
                    'team': str(payload.get('team') or 'Alpha'),
                    'name': str(payload.get('name') or f'Sprint {next_iteration}'),
                    'status': status_text,
                    'completion': int(payload.get('completion') or (15 if status_text == 'active' else 0)),
                    'due': str(payload.get('due') or now_iso),
                    'goals': str(payload.get('goals') or '자동화 사이클 실행'),
                    'createdAt': now_iso,
                }
                rows.insert(0, new_row)
                del rows[50:]
                return jsonify({'ok': True, 'cycle': new_row}), 201

            limit_arg = request.args.get('limit')
            limit = request.args.get('limit', type=int)
            if limit is not None and limit > 0:
                selected = rows[:limit]
            else:
                selected = list(rows)

            if limit_arg is not None:
                return jsonify({
                    'available': True,
                    'cycles': selected,
                    'count': len(selected),
                    'total': len(rows),
                }), 200
            return jsonify(selected), 200
        except Exception:
            return jsonify([]), 500

    @app.route('/api/v1/chat/messages', methods=['POST'])
    def serve_api_v1_chat_messages():
        """Compatibility endpoint for fallback chat transport."""
        try:
            payload = request.get_json(silent=True) or {}
            room = str(payload.get('room') or 'default')
            text_body = str(payload.get('text') or '').strip()
            if not text_body:
                return jsonify({'ok': False, 'error': 'text is required'}), 400
            message_id = f'msg-{int(time.time() * 1000)}'
            return jsonify({
                'ok': True,
                'message_id': message_id,
                'room': room,
                'text': text_body,
                'received_at': datetime.now(timezone.utc).isoformat(),
            }), 201
        except Exception:
            return jsonify({'ok': False, 'error': 'invalid payload'}), 500

    @app.route('/<string:page>')
    def serve_root_alias(page):
        """Compatibility route for legacy root-level page access."""
        if page.startswith('api/'):
            return jsonify({'error': 'Not found'}), 404

        # Direct file from web root (eg index.html, dashboard.html)
        file_path = web_dir / page
        if file_path.is_file():
            return send_from_directory(web_dir, page)

        # Convenience route for extensionless aliases (eg /dashboard -> /dashboard.html)
        html_path = web_dir / f'{page}.html'
        if html_path.is_file():
            return send_from_directory(web_dir, f'{page}.html')

        # Directory alias support (eg /platform -> /platform/index.html)
        dir_index = web_dir / page / 'index.html'
        if dir_index.is_file():
            return send_from_directory(web_dir / page, 'index.html')

        abort(404)

    # === Security Headers Middleware ===
    @app.after_request
    def add_security_headers(response):
        """Add security headers to every response.

        These headers protect against common web vulnerabilities:
        - XSS (Cross-Site Scripting)
        - Clickjacking (iframe embedding)
        - MIME-type sniffing
        - Insecure transport (in production)
        """
        # Prevent MIME-type sniffing (stops browser from interpreting files as different type)
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking by disallowing iframe embedding
        response.headers['X-Frame-Options'] = 'DENY'

        # Enable browser XSS filter (legacy but still useful for older browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Content Security Policy ??restrict resource loading
        # Allow self-hosted resources, inline styles (needed for many UI frameworks),
        # and specific CDNs used by the frontend
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:*; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # HTTP Strict Transport Security (only effective over HTTPS in production)
        # max-age=31536000 = 1 year; includeSubDomains protects all subdomains
        is_production = os.getenv('ENVIRONMENT', 'development') == 'production'
        if is_production:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )

        # Prevent caching of authenticated API responses
        if request.path.startswith('/api/') and request.method != 'OPTIONS':
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'

        # Remove server identification header (information disclosure)
        response.headers.pop('Server', None)

        # Referrer policy ??don't leak URLs to external sites
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy ??restrict browser features
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=()'
        )

        # Inject unified UI assets into served HTML pages (non-API).
        # This gives a consistent style, bigger base typography, and dark mode support
        # across legacy pages without per-file edits.
        content_type = response.headers.get('Content-Type', '')
        is_html = 'text/html' in content_type.lower()
        if is_html and not request.path.startswith('/api/'):
            try:
                response.direct_passthrough = False
                html = response.get_data(as_text=True)
                html_lower = html.lower()

                injections = []
                if '<meta charset=' not in html_lower:
                    injections.append('<meta charset="UTF-8">')
                if 'unified-ui.css' not in html_lower:
                    injections.append('<link rel="stylesheet" href="/unified-ui.css">')
                if 'responsive-framework.css' not in html_lower:
                    injections.append('<link rel="stylesheet" href="/responsive-framework.css">')
                if 'unified-ui.js' not in html_lower:
                    injections.append('<script src="/unified-ui.js" defer></script>')
                if 'mobile-optimization.js' not in html_lower:
                    injections.append('<script src="/mobile-optimization.js" defer></script>')

                if injections:
                    snippet = '\n  '.join(injections)
                    if '</head>' in html:
                        html = html.replace('</head>', f'  {snippet}\n</head>', 1)
                    elif '<body' in html:
                        html = f'{snippet}\n{html}'
                    response.set_data(html)
            except Exception:
                pass

        return response

    # === HTTPS Enforcement Middleware ===
    @app.before_request
    def enforce_https():
        """Redirect HTTP to HTTPS in production.

        Checks both request.is_secure and the X-Forwarded-Proto header
        (set by nginx/load balancer when the original request was HTTPS).
        """
        if (
            os.getenv('ENVIRONMENT', '').strip().lower() == 'production'
            and not app.debug
            and not app.config.get('TESTING')
        ):
            # X-Forwarded-Proto is set by nginx proxy to indicate original scheme
            forwarded_proto = request.headers.get('X-Forwarded-Proto', '')
            if not request.is_secure and forwarded_proto != 'https':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)

    # Initialize database
    with app.app_context():
        init_db(app)
        init_rbac()

    # Validate configuration on startup (warns about missing env vars)
    validate_config(app)

    # Initialize background scheduler (data pipeline jobs)
    # Only start if not in testing mode and not in reloader child process
    if not app.config.get('TESTING') and os.getenv('WERKZEUG_RUN_MAIN') != 'true':
        try:
            from .scheduler import init_scheduler
            init_scheduler(app)
        except Exception as e:
            import logging
            logging.getLogger('scheduler').error(f'Failed to start scheduler: {e}')

        # Start SNS scheduled-post publisher (checks every 60s)
        try:
            from .services.sns_scheduler import start_scheduler as start_sns_scheduler
            start_sns_scheduler(app, interval_seconds=60)
        except Exception as e:
            import logging
            logging.getLogger('sns.scheduler').error(f'Failed to start SNS scheduler: {e}')

    # Initialize WebSocket server for real-time notifications
    try:
        socketio = init_websocket(app)
        app.socketio = socketio
        import logging
        logging.getLogger('websocket').info('WebSocket server initialized successfully')
    except Exception as e:
        import logging
        logging.getLogger('websocket').error(f'Failed to initialize WebSocket: {e}')

    return app


if __name__ == '__main__':
    app = create_app()
    # Use socketio.run() instead of app.run() to enable WebSocket support
    if hasattr(app, 'socketio'):
        app.socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)
    else:
        app.run(host='0.0.0.0', port=8000, debug=True)
