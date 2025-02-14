import warnings
from sqlalchemy import exc as sa_exc

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import timedelta
from config import config

# Suppress SQLAlchemy warnings
warnings.filterwarnings('ignore', category=sa_exc.SAWarning)
warnings.filterwarnings('ignore', r'.*Legacy API.*')

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Auto Shop API"
    }
)

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = 'dev-secret-key'  # Change in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    with app.app_context():
        # Create database tables
        db.create_all()
    
    # JWT handlers
    @jwt.user_identity_loader
    def user_identity_lookup(identity):
        from app.models import User
        if isinstance(identity, User):
            return {
                'id': str(identity.id),
                'is_admin': identity.is_admin
            }
        return str(identity) if identity else None

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        try:
            identity = jwt_data["sub"]
            if isinstance(identity, dict):
                user_id = int(identity['id'])
            else:
                user_id = int(identity)
            from app.models import User
            return db.session.get(User, user_id)
        except (ValueError, TypeError, KeyError):
            return None

    # Error handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": str(e.description)
        }), 429
    
    # Register blueprints
    register_blueprints(app)
    
    return app

def register_blueprints(app):
    from app.components.blueprints.users import user_bp  # Import from __init__.py
    from app.components.blueprints.mechanics import mechanic_bp
    from app.components.blueprints.service_tickets import service_ticket_bp
    from app.components.blueprints.inventory import inventory_bp 
    
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(mechanic_bp, url_prefix='/mechanics')
    app.register_blueprint(service_ticket_bp, url_prefix='/service-tickets')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)