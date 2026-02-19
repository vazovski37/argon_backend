"""
Argonauts Backend - Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from app.extensions import db, jwt, migrate
from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.game import game_bp
    from app.api.locations import locations_bp
    from app.api.quests import quests_bp
    from app.api.photos import photos_bp
    from app.api.rag import rag_bp
    from app.api.groups import groups_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(game_bp, url_prefix='/api/game')
    app.register_blueprint(locations_bp, url_prefix='/api/locations')
    app.register_blueprint(quests_bp, url_prefix='/api/quests')
    app.register_blueprint(photos_bp, url_prefix='/api/photos')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'argonauts-backend'}
    
    # Create tables on first request (dev only)
    with app.app_context():
        db.create_all()
    
    return app





