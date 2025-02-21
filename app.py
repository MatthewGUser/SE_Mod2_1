import os
from app import create_app, db
from config import config
from app.models import User, Mechanic, ServiceTicket
from flask import render_template
from flask_cors import CORS

def create_flask_app():
    """Factory function to create and configure the Flask application"""
    env = os.getenv('FLASK_ENV', 'dev')
    
    if env not in config:
        print(f"Warning: Environment '{env}' not found, using 'dev'")
        env = 'dev'
    
    app = create_app(config[env])
    
    with app.app_context():
        db.create_all()
        print('Database initialized!')
    
    # Enable CORS
    CORS(app)
    
    return app

app = create_flask_app()

@app.route('/docs')
def swagger_ui():
    return render_template('swagger.html')

if __name__ == '__main__':
    print(f"Running in {os.getenv('FLASK_ENV', 'dev')} mode")
    app.run(debug=True, port=5000)