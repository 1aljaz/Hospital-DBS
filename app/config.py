# app/config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # SQLite database in /instance folder
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, '..', 'instance', 'hospital.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
