# app/__init__.py
from flask import Flask
from .db import db
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")  # Load config.py

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    #Login/logout auth
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)


    return app
