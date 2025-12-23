from app.db import db

class Staff(db.Model):
    __tablename__ = "staff"

    staff_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), unique=True)
    role = db.Column(db.String)  # e.g., "doctor" or "admin"
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))

    # Relationships
    appointments = db.relationship("Appointment", backref="staff")
    department = db.relationship("Department", backref="staff_members")
