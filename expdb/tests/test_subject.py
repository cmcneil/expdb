from ..models import Subject
from sqlalchemy.exc import IntegrityError
import pytest


# Test Subject: Ensure a Subject cannot be created without required fields
def test_subject_missing_required_fields(session):
    '''Test that creating a subject without required fields raises an error.'''
    with pytest.raises(IntegrityError):
        subject = Subject(name=None, code="XX", age=25, meditation_experience=3)
        session.add(subject)
        session.commit()
    
    # Rollback the session after failure
    session.rollback()

# Test Subject: Valid subject creation
def test_subject_valid_creation(session):
    '''Test valid creation of a Subject.'''
    subject = Subject(name="Valid Subject", code="VS", age=30, meditation_experience=2)
    session.add(subject)
    session.commit()

    retrieved_subject = session.query(Subject).first()
    assert retrieved_subject.name == "Valid Subject"
    assert retrieved_subject.code == "VS"
    assert retrieved_subject.age == 30