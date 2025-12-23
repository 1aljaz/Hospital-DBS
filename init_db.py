import os
from app import create_app
from app.db import db

# Ensure the /instance folder exists
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(instance_path, exist_ok=True)

app = create_app()

with app.app_context():
    # Import all models here so SQLAlchemy knows about them
    from app.models import User, Patient, Staff, Department, Room, Bed, Appointment, Admission, Diagnosis

    # Create all tables
    db.create_all()
    print(f"Database initialized successfully in {instance_path}/hospital.db")
