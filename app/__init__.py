from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")  # your Flask config

    # You can register blueprints here if you have any
    # from .routes import main
    # app.register_blueprint(main)

    return app
