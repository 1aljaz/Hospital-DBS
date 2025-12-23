# app/models/appointment.py
from app.db import db

class Appointment(db.Model):
    __tablename__ = "appointments"

    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.patient_id"))
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.staff_id"))
    appointment_date = db.Column(db.Date)
    appointment_time = db.Column(db.Time)
    status = db.Column(db.String)

    # Relationships
    patient = db.relationship("Patient", back_populates="appointments")
    staff_member = db.relationship("Staff", back_populates="appointments")
    diagnoses = db.relationship("Diagnosis", back_populates="appointment")
