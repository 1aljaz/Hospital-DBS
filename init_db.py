# init_db.py
from app import create_app
from app.db import db

app = create_app()

with app.app_context():
    # Create all tables based on SQLAlchemy models
    db.create_all()
    print("Database initialized successfully with all tables!")
