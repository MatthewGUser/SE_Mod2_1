from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# Initialize extensions
db = SQLAlchemy()
cache = Cache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Explicitly set memory storage
)

def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Initialize extensions
    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    # Register error handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": str(e.description)
        }), 429
    
    # Register blueprints
    from app.blueprints.users import user_bp
    from app.blueprints.mechanics import mechanic_bp
    from app.blueprints.service_tickets import service_ticket_bp
    from app.blueprints.inventory import inventory_bp
    
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(mechanic_bp, url_prefix='/mechanics')
    app.register_blueprint(service_ticket_bp, url_prefix='/service-tickets')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    return app