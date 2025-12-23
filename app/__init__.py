from flask import Flask
from flask_migrate import Migrate
from .db import db

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)
    Migrate(app, db)

    return app
