from app.db import db

class Bed(db.Model):
    __tablename__ = "beds"

    bed_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.room_id"))
    status = db.Column(db.String)

    # Relationships
    admissions = db.relationship("Admission", backref="bed")
