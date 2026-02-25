"""SoftFactory Flask Application"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path

from .models import db, init_db
from .auth import auth_bp
from .payment import payment_bp
from .platform import platform_bp
from .services.coocook import coocook_bp
from .services.sns_auto import sns_bp
from .services.review import review_bp
from .services.ai_automation import ai_automation_bp
from .services.webapp_builder import webapp_builder_bp


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
    app.register_blueprint(coocook_bp)
    app.register_blueprint(sns_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(ai_automation_bp)
    app.register_blueprint(webapp_builder_bp)

    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'}), 200

    # Serve static files
    web_dir = Path(__file__).parent.parent / 'web'

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
