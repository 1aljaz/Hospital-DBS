# app/models/user.py
from app.db import db
import enum

class RoleEnum(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    password_hash = db.Column(db.String, nullable=False)
    phone = db.Column(db.String)
    role = db.Column(db.Enum(RoleEnum), nullable=False)

    # Relationships
    patient = db.relationship("Patient", back_populates="user", uselist=False)
    staff = db.relationship("Staff", back_populates="user", uselist=False)

    # Helper methods
    def is_admin(self):
        return self.role == RoleEnum.ADMIN

    def is_doctor(self):
        return self.role == RoleEnum.DOCTOR

    def is_patient(self):
        return self.role == RoleEnum.PATIENT
