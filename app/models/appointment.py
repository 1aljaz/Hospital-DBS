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
    diagnoses = db.relationship("Diagnosis", backref="appointment")
