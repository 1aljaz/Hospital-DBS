from app.db import db

class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    location = db.Column(db.String)

    # Relationships
    staff_members = db.relationship("Staff", backref="department", lazy=True)
    rooms = db.relationship("Room", backref="department")
