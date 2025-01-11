import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import (
    Study, Subject, Timecourse, Data, Modality, DataType, TransformData
)
from ..lib.queries import get_latest_timecourses_by_modality

def create_timecourse(session, subject, study, modality, type_, sampling_rate,
                     path, date_collected, transform_names=None,
                     transform_params=None):
    """Helper function to create a timecourse with default values"""
    if transform_names is None:
        transform_names = ["TestTransform"]
    if transform_params is None:
        transform_params = [{}]
    
    data = Data(
        sampling_rate=sampling_rate,
        modality=modality,
        type=type_
    )
    
    transform = TransformData(
        transform_names_json="[]",
        transform_params_json="[]",
        git_commit="test123"
    )
    
    tc = Timecourse(
        subject=subject,
        study=study,
        data=data,
        transform=transform,
        path=path,
        date_collected=date_collected
    )
    session.add(tc)
    return tc

@pytest.fixture
def test_data(session):
    """Create a test dataset with a known DAG structure"""
    # Create a study and subject
    study = Study(name="Test Study", github_repo="test/repo")
    subject = Subject(
        name="Test Subject",
        code="TS",
        age=25,
        meditation_experience=2
    )
    session.add_all([study, subject])
    session.flush()

    # Create base time for our timecourses
    base_time = datetime(2024, 1, 1, 12, 0)
    
    # Create two original EEG uploads
    eeg_upload1 = create_timecourse(
        session, subject, study,
        Modality.IMAGING, DataType.EEG, 256.0,
        "/data/eeg_upload1.eeg",
        base_time
    )
    
    eeg_upload2 = create_timecourse(
        session, subject, study,
        Modality.IMAGING, DataType.EEG, 256.0,
        "/data/eeg_upload2.eeg",
        base_time + timedelta(days=1)
    )
    
    # Create derivatives from eeg_upload1
    eeg_proc1 = create_timecourse(
        session, subject, study,
        Modality.IMAGING, DataType.EEG, 256.0,
        "/data/eeg_proc1.eeg",
        base_time + timedelta(hours=1)
    )
    eeg_proc1.derived_from.append(eeg_upload1)
    
    eeg_proc2 = create_timecourse(
        session, subject, study,
        Modality.IMAGING, DataType.EEG, 256.0,
        "/data/eeg_proc2.eeg",
        base_time + timedelta(hours=2)
    )
    eeg_proc2.derived_from.append(eeg_proc1)
    
    # Create a behavioral upload and derivative
    beh_upload = create_timecourse(
        session, subject, study,
        Modality.BEHAVIORAL, DataType.INPUT_RESPONSE, 60.0,
        "/data/beh_upload.csv",
        base_time
    )
    
    beh_proc = create_timecourse(
        session, subject, study,
        Modality.BEHAVIORAL, DataType.INPUT_RESPONSE, 60.0,
        "/data/beh_proc.csv",
        base_time + timedelta(hours=1)
    )
    beh_proc.derived_from.append(beh_upload)
    
    session.commit()
    
    return {
        'study': study,
        'subject': subject,
        'eeg_upload1': eeg_upload1,
        'eeg_upload2': eeg_upload2,
        'eeg_proc1': eeg_proc1,
        'eeg_proc2': eeg_proc2,
        'beh_upload': beh_upload,
        'beh_proc': beh_proc
    }

def test_get_latest_timecourses_by_modality(session, test_data):
    """Test getting latest timecourses for a subject by modality"""
    subject = test_data['subject']
    
    # Test getting latest EEG timecourses
    latest_eeg = get_latest_timecourses_by_modality(
        session, subject, Modality.IMAGING
    )
    
    assert len(latest_eeg) == 2  # Should get two timecourses
    
    # The latest derivative of eeg_upload1 should be eeg_proc2
    assert test_data['eeg_proc2'] in latest_eeg
    
    # eeg_upload2 has no derivatives, so should be included as-is
    assert test_data['eeg_upload2'] in latest_eeg
    
    # Test getting latest behavioral timecourses
    latest_beh = get_latest_timecourses_by_modality(
        session, subject, Modality.BEHAVIORAL
    )
    
    assert len(latest_beh) == 1  # Should get one timecourse
    assert latest_beh[0] == test_data['beh_proc']  # Should be the processed version

def test_get_latest_timecourses_empty_modality(session, test_data):
    """Test getting latest timecourses for a modality with no data"""
    subject = test_data['subject']
    
    # Test getting latest STIMULUS timecourses (none exist)
    latest = get_latest_timecourses_by_modality(
        session, subject, Modality.STIMULUS
    )
    
    assert len(latest) == 0  # Should get empty list

def test_get_latest_timecourses_no_derivatives(session):
    """Test getting latest timecourses when there are only original uploads"""
    # Create a study and subject
    study = Study(name="No Derivatives", github_repo="test/repo")
    subject = Subject(
        name="Test Subject",
        code="ND",
        age=25,
        meditation_experience=2
    )
    session.add_all([study, subject])
    
    # Create a single upload with no derivatives
    upload = create_timecourse(
        session, subject, study,
        Modality.IMAGING, DataType.EEG, 256.0,
        "/data/solo_upload.eeg",
        datetime.now()
    )
    
    session.commit()
    
    latest = get_latest_timecourses_by_modality(
        session, subject, Modality.IMAGING
    )
    
    assert len(latest) == 1
    assert latest[0] == upload 