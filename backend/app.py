"""SoftFactory Flask Application"""
from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
from pathlib import Path

from .models import db, init_db
from .auth import auth_bp
from .payment import payment_bp
from .platform import platform_bp
from .jarvis_api import jarvis_bp
from .error_api import error_bp
from .services.coocook import coocook_bp
from .services.sns_auto import sns_bp
from .services.review import review_bp
from .services.ai_automation import ai_automation_bp
from .services.webapp_builder import webapp_builder_bp
from .services.experience import experience_bp


def create_app():
    """Application factory"""
    app = Flask(__name__)

    # Configuration
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'platform.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": [
        "http://localhost:5000",
        "http://localhost:8000",
        "null"
    ]}})

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(platform_bp)
    app.register_blueprint(jarvis_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(coocook_bp)
    app.register_blueprint(sns_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(ai_automation_bp)
    app.register_blueprint(webapp_builder_bp)
    app.register_blueprint(experience_bp)

    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'}), 200

    # Infrastructure health check endpoint
    @app.route('/api/infrastructure/health')
    def infrastructure_health():
        """Comprehensive system health check"""
        import time
        from .models import User

        try:
            # Check database
            db_status = 'ok'
            try:
                User.query.first()
            except Exception:
                db_status = 'error'

            # Calculate uptime (placeholder)
            uptime = '24h 15m'

            return jsonify({
                'overall_status': 'healthy' if db_status == 'ok' else 'degraded',
                'api_status': 'ok',
                'database_status': db_status,
                'uptime': uptime,
                'timestamp': time.time()
            }), 200
        except Exception as e:
            return jsonify({
                'overall_status': 'unhealthy',
                'api_status': 'error',
                'database_status': 'error',
                'error': str(e)
            }), 500

    # Process list endpoint
    @app.route('/api/infrastructure/processes')
    def infrastructure_processes():
        """Get active process information"""
        try:
            processes = []

            # Current Python process (basic info)
            processes.append({
                'name': 'Flask API',
                'pid': os.getpid(),
                'status': 'running'
            })

            return jsonify({
                'processes': processes,
                'total_count': len(processes)
            }), 200
        except Exception as e:
            return jsonify({
                'processes': [],
                'error': str(e)
            }), 500

    # Serve static files - use absolute Windows path
    import sys
    if sys.platform == 'win32':
        # Windows path
        web_dir = Path('D:\\Project\\web')
    else:
        # Unix path
        current_dir = Path(__file__).parent.parent
        web_dir = current_dir / 'web'

    # Ensure path exists
    if not web_dir.exists():
        # Try alternative paths
        alt_paths = [
            Path('D:/Project/web'),
            Path(__file__).parent.parent / 'web',
            Path.cwd() / 'web'
        ]
        for alt in alt_paths:
            if alt.exists():
                web_dir = alt
                break

    @app.route('/')
    def index():
        """Serve main platform dashboard"""
        platform_index = web_dir / 'platform' / 'index.html'
        if platform_index.exists():
            return send_file(str(platform_index))
        return jsonify({'error': 'Platform index not found'}), 404

    @app.route('/<path:path>')
    def serve_main(path):
        """Serve files from web directory with fallback to index.html"""
        # Try exact file
        file_path = web_dir / path
        if file_path.is_file():
            return send_file(str(file_path))

        # Try directory with index.html
        if file_path.is_dir():
            index_file = file_path / 'index.html'
            if index_file.is_file():
                return send_file(str(index_file))

        # Try with .html extension
        html_file = file_path.parent / (file_path.name + '.html')
        if html_file.is_file():
            return send_file(str(html_file))

        # Fallback to main index for SPA routing
        platform_index = web_dir / 'platform' / 'index.html'
        if platform_index.exists():
            return send_file(str(platform_index))

        return jsonify({'error': 'Not found'}), 404

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

    # Initialize database
    with app.app_context():
        init_db(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)
