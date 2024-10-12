from ..models import Study
from sqlalchemy.exc import IntegrityError
import pytest


# Test Study: Valid Study creation
def test_study_valid_creation(session):
    '''Test valid creation of a Study.'''
    study = Study(name="Valid Study", github_repo="valid/repo")
    session.add(study)
    session.commit()

    retrieved_study = session.query(Study).first()
    assert retrieved_study.name == "Valid Study"
    assert retrieved_study.github_repo == "valid/repo"

# Test Study: Missing non-nullable field
def test_study_missing_required_fields(session):
    '''Test that creating a Study without a required field raises an error.'''
    with pytest.raises(IntegrityError):
        study = Study(name=None, github_repo="test/repo")
        session.add(study)
        session.commit()

    session.rollback()