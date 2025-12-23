# app/config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # SQLite database in /instance folder
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, '..', 'instance', 'hospital.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "f3b1c2d4e5a67890b1c2d3e4f5a67890b1c2d3e4f5a67890"
