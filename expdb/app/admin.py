from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms_sqlalchemy.fields import QuerySelectMultipleField

import json


from ..models import Study, Subject, Timecourse

class StudyAdmin(ModelView):
    # Display subjects as a multi-select dropdown
    form_columns = ['name', 'description', 'github_repo',
                    'subjects', 'created_at', ]
    
    # Searchable columns
    column_searchable_list = ['name', 'description']

    # Filterable columns
    column_filters = ['name', 'description']

    # Sortable columns
    column_sortable_list = ['name', 'description', 'created_at']

    # Customize the columns displayed in the list view
    column_list = ['name', 'description', 'github_repo', 'subjects']
    
    def form_subjects(self):
        return QuerySelectMultipleField(
            'Subjects',
            query_factory=lambda: self.session.query(Subject),
            get_label='code'
        )

class SubjectAdmin(ModelView):
    # Display studies as a multi-select dropdown
    form_columns = ['name', 'code','age', 'studies']

    column_searchable_list = ['name', 'code']

    # Filterable columns
    column_filters = ['name', 'code', 'age']

    # Sortable columns
    column_sortable_list = ['name', 'code', 'age']

    # Customize the columns displayed in the list view
    column_list = ['name', 'code', 'age', 'studies']
    
    def form_studies(self):
        return QuerySelectMultipleField(
            'Studies',
            query_factory=lambda: self.session.query(Study),
            get_label='name'
        )
    
class MyAdminIndexView(AdminIndexView):

    def __init__(self, session):
        super().__init__()
        self.session = session

    @expose('/')
    def index(self):
        # You can query your database for stats
        study_count = self.session.query(Study).count()
        subject_count = self.session.query(Subject).count()
        timecourse_count = self.session.query(Timecourse).count()

        timecourses = self.session.query(Timecourse).all()
        timecourse_data = [
            {
                'id': timecourse.id,
                'label': f'Timecourse {timecourse.id}',
                'sampling_rate': timecourse.data.sampling_rate,
                'path': timecourse.data.path,
                'description': timecourse.data.description,
                'modality': timecourse.data.modality.name,
                'type': timecourse.data.type.name,
                'is_pilot': timecourse.is_pilot,
                'transform_names': json.loads(timecourse.transform.transform_names_json),
                'derived_from': [parent.id 
                                 for parent in timecourse.derived_from]
            }
            for timecourse in timecourses
        ]

        # Pass the data to your custom template
        return self.render('dashboard.html', study_count=study_count,
                           subject_count=subject_count,
                           timecourse_count=timecourse_count,
                           timecourse_data=timecourse_data)


def init_admin(app):
    # Initialize the Flask-Admin extension
    admin = Admin(app, name='Research Admin', template_mode='bootstrap3',
                  index_view=MyAdminIndexView(app.session))

    # Add SQLAlchemy models to the admin interface
    admin.add_view(SubjectAdmin(Subject, app.session))
    admin.add_view(StudyAdmin(Study, app.session))
