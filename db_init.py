from app import create_app, db
from app.models import User

def init_db():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                name='Admin User',
                email='admin@example.com',
                phone='123-456-7890',
                is_admin=True
            )
            admin.set_password('AdminPass123!')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()