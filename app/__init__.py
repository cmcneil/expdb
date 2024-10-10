from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.orm import scoped_session
from db import Session
from .admin import init_admin  # Import the admin panel setup

def create_app():
    app = Flask(__name__)

    # Setup the session for the app
    app.session = scoped_session(Session)

    # Initialize Flask-Admin
    init_admin(app)

    # Basic route for testing
    @app.route('/')
    def index():
        return "Welcome to the Research Admin Panel!"

    return app
