# app/models/bed.py
from app.db import db

class Bed(db.Model):
    __tablename__ = "beds"

    bed_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.room_id"))
    status = db.Column(db.String)

    # Relationships
    room = db.relationship("Room", back_populates="beds")
    admissions = db.relationship("Admission", back_populates="bed")
