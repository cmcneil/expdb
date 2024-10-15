from sqlalchemy.orm import relationship, declarative_base, mapped_column
from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.sql import func

from . import Base
from .relations import study_subject_association


# Study model - represents the overall research study
class Study(Base):
    __tablename__ = 'studies'
    
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(255), nullable=False, unique=True)
    description = mapped_column(Text, nullable=True)
    github_repo = mapped_column(String(255), nullable=False)
    created_at = mapped_column(DateTime, server_default=func.now())
    
    # Many-to-many relationship with subjects through an association table
    subjects = relationship("Subject", secondary=study_subject_association,
                            back_populates="studies")
    
    # One study can have many timecourses
    timecourses = relationship("Timecourse", back_populates="study",
                               cascade="all, delete-orphan")
