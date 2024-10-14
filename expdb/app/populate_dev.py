import json
from . import create_app, db
from ..models import Study, Subject, Timecourse, Modality, DataType, Data, TransformData
from sqlalchemy.exc import SQLAlchemyError

def populate_dev_data():
    db.flush_db()
    db.init_db()

    session = db.Session()

    try:      
        # Add a single test study and subject
        study = Study(name="Test Study", description="A study for testing",
                      github_repo="test/repo")
        subject = Subject(name="Test Subject", code="T1", age=25,
                          meditation_experience=4)

        # Add basic transform data
        transform_data1 = TransformData(
            transform_names_json=json.dumps(["TransformA", "TransformB"]),
            transform_params_json=json.dumps([{"param1": 10}, {"param2": 20}]),
            git_commit="abc123"
        )
        
        transform_data2 = TransformData(
            transform_names_json=json.dumps(["TransformC"]),
            transform_params_json=json.dumps([{"param3": 5}]),
            git_commit="def456"
        )

        # Timecourse data
        data1 = Data(sampling_rate=1000, path="gs://bucket/path1", 
                     modality=Modality.IMAGING, type=DataType.EEG,
                     description="EEG Timecourse")
        data2 = Data(sampling_rate=500, path="gs://bucket/path2", 
                     modality=Modality.BEHAVIORAL, type=DataType.INPUT_RESPONSE,
                     description="Behavioral Timecourse")

        data3 = Data(sampling_rate=250, path="gs://bucket/path3", 
                     modality=Modality.STIMULUS, type=DataType.VIDEO,
                     description="Stimulus Timecourse")

        # Create a chain of Timecourses forming a 4-link deep DAG structure
        # All timecourses remain under the same study and subject
        timecourse1 = Timecourse(data=data1, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True)
        
        timecourse2 = Timecourse(data=data2, transform=transform_data2,
                                 study=study, subject=subject, _is_pilot=True)
        
        timecourse3 = Timecourse(data=data3, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True)
        
        # Establish relationships between timecourses
        timecourse2.derived_from.append(timecourse1)  # timecourse2 is derived from timecourse1
        timecourse3.derived_from.append(timecourse2)  # timecourse3 is derived from timecourse2

        # Add more timecourses to form a 4-link deep DAG
        timecourse4 = Timecourse(data=data1, transform=transform_data2,
                                 study=study, subject=subject, _is_pilot=True)
        timecourse4.derived_from.append(timecourse3)  # timecourse4 is derived from timecourse3
        
        timecourse5 = Timecourse(data=data2, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True)
        
        timecourse6 = Timecourse(data=data2, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True)
        timecourse6.derived_from.append(timecourse2)  # timecourse5 is derived from timecourse4
        timecourse4.derived_from.append(timecourse6) 

        # Commit everything to the database
        session.add_all([study, subject, timecourse1, timecourse2, timecourse3, 
                         timecourse4, timecourse5, timecourse6])
        session.commit()
        print("Development database populated with test data including timecourses!")
    except SQLAlchemyError as e:
        print(f"Error occurred: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print(db.config.SQLALCHEMY_DATABASE_URI)
    populate_dev_data()
