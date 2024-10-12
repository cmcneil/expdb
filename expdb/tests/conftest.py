from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import Base

import pytest

# Use an in-memory SQLite database for fast tests
@pytest.fixture(scope="session")
def engine():
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope="function")
def tables(engine):
    # Base.metadata.clear()
    # Create all tables in the in-memory SQLite database
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def session(engine, tables):
    """Creates a new session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
