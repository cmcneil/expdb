from sqlalchemy import Column, Table, ForeignKey

from . import Base  # Import Base to ensure it is mapped correctly

study_subject_association = Table(
    'study_subject_association',
    Base.metadata,
    Column('study_id', ForeignKey('studies.id'), primary_key=True),
    Column('subject_id', ForeignKey('subjects.id'), primary_key=True)
)
