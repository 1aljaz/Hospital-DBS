# app/models/patient.py
from app.db import db

class Patient(db.Model):
    __tablename__ = "patients"

    patient_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), unique=True)
    gender = db.Column(db.String)
    address = db.Column(db.String)

    # Relationships
    user = db.relationship("User", back_populates="patient")
    appointments = db.relationship("Appointment", back_populates="patient")
    admissions = db.relationship("Admission", back_populates="patient")
