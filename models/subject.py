from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, relationship

from . import Base
from .relations import study_subject_association  # Import association table



class Subject(Base):
  _tablename__ = 'subjects'

  id = mapped_column(Integer, primary_key=True)
  code = mapped_column(String(255), nullable=False) # Two-character, i.e. "JH"
  name = mapped_column(String(255)) # Full name
  age = mapped_column(Integer) # Years
  meditation_experience = mapped_column(Integer) # Years

  # Studies the subject is in.
  studies = relationship("Study", secondary=study_subject_association,
                          back_populates="subjects")
  
  # timecourses collected from the subject
  timecourses = relationship("Timecourse", back_populates="subject",
                             cascade="all, delete-orphan")
