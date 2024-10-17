import json

from .. import db
from ..config import get_config
from ..models import Base, Study, Subject, Timecourse, Modality, DataType, Data, TransformData

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


CONFIG = get_config()

def populate_dev_data():

    # db.flush_db()
    # db.init_db()

    # session = db.Session()
    test_engine = create_engine(CONFIG.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=test_engine)
    session = Session()
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)

    try:      
        # Add a single test study and subject
        study = Study(name="Test Study", description="A study for testing",
                      github_repo="test/repo")
        study2 = Study(name="Test Study 2", 
                       description="A second study for testing",
                       github_repo="test/repo2")
        subject = Subject(name="Test Subject", code="T1", age=25,
                          meditation_experience=4)
        subject2 = Subject(name="Test Subject", code="T2", age=28,
                          meditation_experience=2)

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
        data1 = Data(sampling_rate=1000,  
                     modality=Modality.IMAGING, type=DataType.EEG)
        data2 = Data(sampling_rate=500,
                     modality=Modality.BEHAVIORAL, type=DataType.INPUT_RESPONSE)

        data3 = Data(sampling_rate=250,
                     modality=Modality.STIMULUS, type=DataType.VIDEO)

        # Create a chain of Timecourses forming a 4-link deep DAG structure
        # All timecourses remain under the same study and subject
        timecourse1 = Timecourse(data=data1, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True,
                                 path="gs://bucket/path1",
                                 description="EEG Timecourse")
        
        timecourse2 = Timecourse(data=data2, transform=transform_data2,
                                 study=study, subject=subject, _is_pilot=True,
                                 path="gs://bucket/path2",
                                 description="Behavioral Timecourse")
        
        timecourse3 = Timecourse(data=data3, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True,
                                 path="gs://bucket/path3",
                                 description="Stimulus Timecourse")
        
        # Establish relationships between timecourses
        timecourse2.derived_from.append(timecourse1)  # timecourse2 is derived from timecourse1
        timecourse3.derived_from.append(timecourse2)  # timecourse3 is derived from timecourse2

        # Add more timecourses to form a 4-link deep DAG
        timecourse4 = Timecourse(data=data1, transform=transform_data2,
                                 study=study, subject=subject, _is_pilot=True,
                                 path="gs://bucket/path4",
                                 description="EEG Timecourse Preprocessed")
        timecourse4.derived_from.append(timecourse3)  # timecourse4 is derived from timecourse3
        
        timecourse5 = Timecourse(data=data2, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True,
                                 path="gs://bucket/path5",
                                 description="Behavioral Timecourse Preprocessed")
        
        timecourse6 = Timecourse(data=data2, transform=transform_data1,
                                 study=study, subject=subject, _is_pilot=True,
                                 path="gs://bucket/path6",
                                 description="Behavioral Timecourse Preprocessed")
        timecourse6.derived_from.append(timecourse2)  # timecourse5 is derived from timecourse4
        timecourse4.derived_from.append(timecourse6) 

        # Commit everything to the database
        session.add_all([study, subject, study2, subject2,
                         timecourse1, timecourse2, timecourse3, 
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
