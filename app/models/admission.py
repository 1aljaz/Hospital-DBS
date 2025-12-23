# app/models/admission.py
from app.db import db

class Admission(db.Model):
    __tablename__ = "admissions"

    admission_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.patient_id"))
    bed_id = db.Column(db.Integer, db.ForeignKey("beds.bed_id"))
    admitted_date = db.Column(db.Date)
    discharged_date = db.Column(db.Date, nullable=True)

    # Relationships
    patient = db.relationship("Patient", back_populates="admissions")
    bed = db.relationship("Bed", back_populates="admissions")
