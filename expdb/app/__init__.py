from flask import Flask, request, redirect, url_for, render_template, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
# from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from wtforms import SubmitField
from wtforms_sqlalchemy.orm import model_form


from ..config import get_config
# from ..db import Session
from ..models import Base, Subject, Study


from .admin import init_admin  # Import the admin panel setup


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Setup the session for the app
    # app.session = scoped_session(Session)
    db = SQLAlchemy(app, model_class=Base)
    app.db = db
    
    with app.app_context():
        engine = db.engine
        Base.metadata.bind = engine
        Base.metadata.create_all(engine)

    # Initialize Flask-Admin
    init_admin(app, db)

    # Form objects.
    SubjectForm = model_form(Subject, base_class=FlaskForm,
                             db_session=db.session)
    class SubmitSubjectForm(SubjectForm):
        submit = SubmitField('Submit')
    StudyForm = model_form(Study, base_class=FlaskForm,
                             db_session=db.session)
    class SubmitStudyForm(StudyForm):
        submit = SubmitField('Submit')

    # Basic route for testing
    @app.route('/')
    def index():
        return "Welcome to the Research Admin Panel!"
    
    # Route to render the form for uploading a Timecourse
    @app.route('/upload_data', methods=['GET', 'POST'])
    def upload_data():
        subject_form = SubmitSubjectForm(request.form)
        study_form = SubmitStudyForm(request.form)
        if request.method == 'POST':
            # Get form data
            subject_id = request.form.get('subject_id')
            study_id = request.form.get('study_id')
            path = request.form.get('path')
            description = request.form.get('description')

            # Assuming process_timecourse handles the logic to create a Timecourse object
            # new_timecourse = process_timecourse(subject_id, study_id, path, description)

            # # Add the new timecourse to the database
            # session.add(new_timecourse)
            # session.commit()

            return redirect(url_for('upload_data'), subject_form=subject_form)  # Redirect back to the form after success

        # Query available subjects and studies for the dropdowns
        subjects = db.session.query(Subject).all()
        studies = db.session.query(Study).all()

        return render_template('upload_data.html', subjects=subjects,
                               studies=studies, subject_form=subject_form,
                               study_form=study_form)

    # API route to handle creation of a new subject or study via AJAX
    @app.route('/create_subject', methods=['POST'])
    def create_subject():
        form = SubmitSubjectForm()
        
        if form.validate_on_submit():
            subject = Subject(name=form.name.data, code=form.code.data,
                              email=form.email.data, age=form.age.data,
                              meditation_experience=form.meditation_experience.data)
            subject.studies.extend(form.studies.data)
            db.session.add(subject)
            try:
                db.session.commit()
            except SQLAlchemyError as e:
                return jsonify(success=False, errors=str(e)), 400
            return jsonify(success=True, message="Form submitted successfully!")
        else:
            return jsonify(success=False, errors=form.errors), 400

    @app.route('/create_study', methods=['POST'])
    def create_study():
        name = request.form.get('name')

        new_study = Study(name=name)
        db.session.add(new_study)
        db.session.commit()

        return jsonify({'success': True, 'study_id': new_study.id, 'study_name': new_study.name})


    return app
