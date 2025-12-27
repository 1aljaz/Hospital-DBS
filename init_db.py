import os
from app import create_app
from app.db import db

# Ensure the /instance folder exists
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(instance_path, exist_ok=True)

app = create_app()

with app.app_context():
    from app.models import User, Patient, Staff, Department, Room, Bed, Appointment, Admission, Diagnosis

    db.create_all()
    print(f"Database initialized successfully in {instance_path}/hospital.db")
