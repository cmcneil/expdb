from sqlalchemy import Table, ForeignKey
from sqlalchemy.orm import mapped_column

from . import Base  # Import Base to ensure it is mapped correctly

study_subject_association = Table(
    'study_subject_association',
    Base.metadata,
    mapped_column('study_id', ForeignKey('studies.id'), primary_key=True),
    mapped_column('subject_id', ForeignKey('subjects.id'), primary_key=True)
)
