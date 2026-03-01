"""SoftFactory Flask Application — Security-Hardened + Production Monitoring"""
from flask import Flask, jsonify, send_from_directory, request, redirect, g
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
from . import oauth
from .config import Config
from .config_validator import validate_config
from .auth import require_auth, require_admin


# Allowed CORS origins — restrict to known frontends only
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

# Alert cooldown — prevent spam (2 min between identical alerts)
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

    # Record start time for uptime calculation (also used by /health and /metrics)
    app._start_time = time.time()

    # Configuration — environment-based database URL
    # Use DATABASE_URL env var if set (PostgreSQL production), otherwise fall back to SQLite (dev)
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # SQLite development default — absolute path prevents duplicate DB creation
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'platform.db')
        db_url = f'sqlite:///{db_path}'
    elif db_url.startswith('postgres://'):
        # Heroku / Railway legacy scheme → SQLAlchemy-compatible scheme
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

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
    migrate = Migrate(app, db)  # noqa: F841 — registers flask db CLI commands

    # Initialise Sentry error tracking (silent no-op when SENTRY_DSN absent)
    from .monitoring import init_sentry
    init_sentry(app)

    # CORS — Hardened configuration
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
                    f'— {duration_ms:.0f} ms (HTTP {status})'
                )

            if status >= 500:
                _maybe_alert_high_error_rate(app)

        except Exception:
            pass  # Telemetry errors must never affect the response

        return response

    # -----------------------------------------------------------------------
    # Health check — comprehensive (Task 2)
    # -----------------------------------------------------------------------

    @app.route('/health')
    def health():
        """Comprehensive health check: DB, scheduler, AI service, memory, uptime."""
        import psutil

        status = {
            'status':    'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version':   os.getenv('APP_VERSION', '1.0.0'),
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
            app.logger.error(f'Health — DB error: {exc}')
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

        # Content Security Policy — restrict resource loading
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

        # Referrer policy — don't leak URLs to external sites
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy — restrict browser features
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=()'
        )

        return response

    # === HTTPS Enforcement Middleware ===
    @app.before_request
    def enforce_https():
        """Redirect HTTP to HTTPS in production.

        Checks both request.is_secure and the X-Forwarded-Proto header
        (set by nginx/load balancer when the original request was HTTPS).
        """
        if not app.debug and not app.config.get('TESTING'):
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
