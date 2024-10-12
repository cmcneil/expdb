from ..models import Data, DataType, Modality, Timecourse, TransformData, Subject, Study
from ..transforms import Transform

from sqlalchemy.exc import IntegrityError, DataError
import pytest

import json

# Test TransformData
#--------------------
class ValidTransform(Transform):
    pass

class InvalidClass:
    pass

def test_timecourse_creation(session):
    """Test basic timecourse creation and retrieval."""
    study = Study(name="Test Study", github_repo="test/repo")
    subject = Subject(name="Testy McTesterson", code="TT",
                      age=20, meditation_experience=5)
    data = Data(
        sampling_rate=256.0,
        path="/data/bucket/scan_001.nii",
        modality=Modality.IMAGING,
        type=DataType.FMRI,
        description="fMRI scan from session 1"
    )
    xfm = TransformData(
        transform_names_json="[]",
        transform_params_json="[]",
        git_commit="1234567"
    )
    timecourse = Timecourse(subject=subject, study=study, is_pilot=True,
                            data=data, transform=xfm)

    # Add and commit to the session
    session.add(timecourse)
    session.commit()

    # Query back the timecourse
    retrieved_timecourse = session.query(Timecourse).first()

    assert retrieved_timecourse is not None
    assert retrieved_timecourse.is_pilot == True
    assert retrieved_timecourse.study.name == "Test Study"
    assert retrieved_timecourse.subject.name == "Testy McTesterson"

def test_timecourse_propagation(session):
    """Test propagation of the is_pilot flag in a timecourse DAG."""
    study = Study(name="Test Study", github_repo="test/repo")
    subject = Subject(name="Testy McTesterson", code="TT",
                      age=20, meditation_experience=5)
    data = Data(
        sampling_rate=256.0,
        path="/data/bucket/scan_001.nii",
        modality=Modality.IMAGING,
        type=DataType.FMRI,
        description="fMRI scan from session 1"
    )
    # Provide valid TransformData
    transform_data = TransformData(
        transform_names_json=json.dumps(["ValidTransform"]),
        transform_params_json=json.dumps([{'param1': 1}]),
        git_commit="abc123"
    )
    timecourse = Timecourse(subject=subject, study=study, is_pilot=True,
                            data=data, transform=transform_data)

    tc1 = Timecourse(subject=subject, study=study, is_pilot=True, data=data,
                     transform=transform_data)
    tc2 = Timecourse(subject=subject, study=study, is_pilot=True, data=data,
                     transform=transform_data)
    tc3 = Timecourse(subject=subject, study=study, is_pilot=True, data=data,
                     transform=transform_data)

    # Establish lineage
    tc2.derived_from.append(tc1)  # tc2 is derived from tc1
    tc3.derived_from.append(tc2)  # tc3 is derived from tc2

    session.add_all([tc1, tc2, tc3])
    print("PROPOGATION 4")
    session.commit()

    # Deactivate tc1
    tc2.is_pilot = False
    session.commit()

    print("PROPOGATION 4")

    # Check that the flag propagated correctly
    assert not tc1.is_pilot
    assert not tc3.is_pilot


# Test Timecourse: Ensure a Timecourse cannot be created without required fields
def test_timecourse_missing_required_fields(session):
    '''Test that creating a timecourse without required fields raises an error.'''
    study = Study(name="Test Study", github_repo="test/repo")
    subject = Subject(name="Testy McTesterson", code="TT",
                      age=20, meditation_experience=5)
    
    # Attempt to create Timecourse without data
    with pytest.raises(IntegrityError):
        timecourse = Timecourse(subject=subject, study=study, is_pilot=True)
        session.add(timecourse)
        session.commit()
    
    # Rollback the session after failure
    session.rollback()

# Test Timecourse: Invalid Enum values in data
def test_timecourse_invalid_enum_values(session):
    '''Test that invalid enum values for Modality and DataType raise errors.'''
    study = Study(name="Test Study", github_repo="test/repo")
    subject = Subject(name="Testy McTesterson", code="TT", age=20, meditation_experience=5)
    
    # Invalid modality
    with pytest.raises(ValueError):
        data = Data(sampling_rate=256.0, path="/data/invalid", modality="INVALID", type=DataType.FMRI)
        transform_data = TransformData(
        transform_names_json=json.dumps(["ValidTransform"]),
            transform_params_json=json.dumps([{'param1': 1}]),
            git_commit="abc123"
        )
        timecourse = Timecourse(subject=subject, study=study, is_pilot=True, data=data,
                                transform=transform_data)
        session.add(timecourse)
        session.commit()
    
    # Rollback the session after failure
    session.rollback()

# Test Timecourse: Valid creation
def test_timecourse_valid_creation(session):
    '''Test valid creation of a Timecourse.'''
    study = Study(name="Test Study", github_repo="test/repo")
    subject = Subject(name="Testy McTesterson", code="TT", age=20, meditation_experience=5)
    data = Data(sampling_rate=256.0, path="/data/valid", modality=Modality.IMAGING, type=DataType.FMRI)
    transform_data = TransformData(
        transform_names_json=json.dumps(["ValidTransform"]),
        transform_params_json=json.dumps([{'param1': 1}]),
        git_commit="abc123"
    )
    timecourse = Timecourse(subject=subject, study=study, is_pilot=True,
                            data=data, transform=transform_data)
    session.add(timecourse)
    session.commit()

    retrieved_timecourse = session.query(Timecourse).first()
    assert retrieved_timecourse.is_pilot == True
    assert retrieved_timecourse.data.modality == Modality.IMAGING
    assert retrieved_timecourse.data.sampling_rate == 256.0




def test_valid_transform_data(session):
    """Test that valid transform data passes the validator."""
    study = Study(name="Valid Study", github_repo="valid/repo")
    subject = Subject(name="Valid Subject", code="VS", age=30, meditation_experience=2)
    
    # Provide valid Data object
    data = Data(
        sampling_rate=256.0,
        path="/data/valid",
        modality=Modality.IMAGING,
        type=DataType.FMRI,
        description="Valid data"
    )
    
    # Provide valid TransformData
    transform_data = TransformData(
        transform_names_json=json.dumps(["ValidTransform"]),
        transform_params_json=json.dumps([{'param1': 1}]),
        git_commit="abc123"
    )
    
    timecourse = Timecourse(subject=subject, study=study, is_pilot=True, data=data, transform=transform_data)
    
    session.add(timecourse)
    session.commit()  # Should not raise any exceptions

def test_malformed_json_transform_params(session):
    """Test that malformed JSON raises a ValueError during validation."""
    study = Study(name="Valid Study", github_repo="valid/repo")
    subject = Subject(name="Valid Subject", code="VS", age=30, meditation_experience=2)
    
    # Provide valid Data object
    data = Data(
        sampling_rate=256.0,
        path="/data/valid",
        modality=Modality.IMAGING,
        type=DataType.FMRI,
        description="Valid data"
    )
    
    # Provide invalid JSON for the params
    with pytest.raises(json.JSONDecodeError):
        transform_data = TransformData(
            transform_names_json=json.dumps(["ValidTransform"]),
            transform_params_json="INVALID_JSON_STRING",
            git_commit="abc123"
        )

