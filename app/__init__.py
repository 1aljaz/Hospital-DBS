# app/__init__.py
from flask import Flask
from .db import db
from flask_migrate import Migrate
from flask_login import LoginManager
from app.models.user import User

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config") 

    #login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = User.query.get(int(user_id))
            if user:
                print(f"User loaded: {user.user_id}, {user.username}, role: {user.role.value}")
            else:
                print(f"User not found for user_id: {user_id}")
            return user
        except Exception as e:
            print(f"Error loading user {user_id}: {e}")
            return None

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Main route
    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    #Login/logout auth
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)


    return app
