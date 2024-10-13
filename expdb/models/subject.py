from __future__ import annotations

from typing import List, TYPE_CHECKING


from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base #, Study, Timecourse
from .relations import study_subject_association  # Import association table

if TYPE_CHECKING:
    from .study import Study  # Import here without causing circular import at runtime
    from .timecourse import Timecourse

class Subject(Base):
  __tablename__ = 'subjects'

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  code: Mapped[str] = mapped_column(String(255), nullable=False) # Two-character, i.e. "JH"
  name: Mapped[str] = mapped_column(String(255)) # Full name
  age: Mapped[int] = mapped_column(Integer) # Years
  meditation_experience: Mapped[int] = mapped_column(Integer) # Years

  # Studies the subject is in.
  studies: Mapped[List[Study]] = relationship(
    "Study", secondary=study_subject_association, back_populates="subjects")
  
  # timecourses collected from the subject
  timecourses: Mapped[List[Timecourse]] = relationship(
    "Timecourse", back_populates="subject", cascade="all, delete-orphan")
