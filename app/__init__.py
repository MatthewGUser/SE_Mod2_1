from flask import Flask
from app.models import db
from .blueprints.user import user_bp
from .extensions import ma, limiter, cache

def create_app(config_name):
    app = Flask(__name__)
    
    # Load app configuration
    app.config.from_object(f'config.{config_name}')
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app
    limiter.init_app(app)
    
    # Register blueprints
    app.register_blueprint(user_bp)
    
    return app