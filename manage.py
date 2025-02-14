from app import create_app, db
from flask.cli import FlaskGroup

cli = FlaskGroup(create_app=create_app)

@cli.command("init_db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')

if __name__ == '__main__':
    cli()