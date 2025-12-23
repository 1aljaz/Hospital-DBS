from app.db import db

class Diagnosis(db.Model):
    __tablename__ = "diagnoses"

    diagnosis_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.appointment_id"))
    description = db.Column(db.String)
