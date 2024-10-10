from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import Study, Subject

def init_admin(app):
    # Initialize the Flask-Admin extension
    admin = Admin(app, name='Research Admin', template_mode='bootstrap3')

    # Add SQLAlchemy models to the admin interface
    admin.add_view(ModelView(Subject, app.session))
    admin.add_view(ModelView(Study, app.session))
