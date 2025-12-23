# app/models/room.py
from app.db import db

class Room(db.Model):
    __tablename__ = "rooms"

    room_id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))

    # Relationships
    department = db.relationship("Department", back_populates="rooms")
    beds = db.relationship("Bed", back_populates="room")
