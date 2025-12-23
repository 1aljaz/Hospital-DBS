from app.db import db

class Patient(db.Model):
    __tablename__ = "patients"

    patient_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), unique=True)
    gender = db.Column(db.String)
    address = db.Column(db.String)

    # Relationships
    appointments = db.relationship("Appointment", backref="patient")
    admissions = db.relationship("Admission", backref="patient")
