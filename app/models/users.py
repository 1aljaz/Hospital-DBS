from app.db import db

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    password_hash = db.Column(db.String, nullable=False)
    phone = db.Column(db.String)

    # Relationships
    patient = db.relationship("Patient", backref="user", uselist=False)
    staff = db.relationship("Staff", backref="user", uselist=False)
