from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy import Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.sql import func

from .base import Base  # Import the Base model

"""
syntax="proto2";

package expdb;

// Next Id: 4
message Modality {
    enum Type {
        UNKNOWN = 0;
        STIMULUS = 1;
        BEHAVIORAL = 2;
        IMAGING = 3;
    }
}

message Datatype {
    enum Type {
        UNKNOWN = 0;
        EEG = 1;
        FMRI = 2;
        INPUT_RESPONSE = 3;
        VISUAL_PROMPT = 4;
        VIDEO = 5;
        AUDITORY_PROMPT = 6;
    }
}
"""

# Association table for Timecourse DAG (many-to-many self-referencing)
timecourse_lineage_association = Table(
    'timecourse_lineage_association',
    Base.metadata,
    mapped_column('derived_timecourse_id', ForeignKey('timecourses.id'),
                  primary_key=True),
    mapped_column('parent_timecourse_id', ForeignKey('timecourses.id'),
                  primary_key=True)
)


class Data:
    def __init__(self, type, modality, sampling_rate, path, description):
        """
        Initialize a Data object.

        Parameters
        ----------
        type : str
            Type of data (e.g. stimulus, behavioral, imaging.)
        modality : str
            Modality of the data (e.g. EEG, MEG, fMRI, etc.)
        sampling_rate : int
            Sampling rate of the data (Hz)
        path : str
            File path to the data's cloud bucket.
        description : str
            Description of the data
        """
        self.modality = modality
        self.type = type
        self.sampling_rate = sampling_rate
        self.path = path
        self.description = description

class Timecourse(Base):
    __tablename__ = 'timecourses'
    
    id = mapped_column(Integer, primary_key=True)
    subject_id = mapped_column(Integer, ForeignKey('subjects.id'), nullable=False)
    study_id = mapped_column(Integer, ForeignKey('studies.id'), nullable=False)
    type = mapped_column(String(100), nullable=False)  # e.g., fMRI, EEG, Behavioral
    date_collected = mapped_column(DateTime, server_default=func.now())
    
    # For data lineage: a timecourse can derive from another timecourse
    derived_from_id = mapped_column(Integer, ForeignKey('timecourses.id'), nullable=True)
    
    # Relationships for data lineage
    derived_from = relationship("Timecourse", remote_side=[id], backref="derived_timecourses")
    
    # Each timecourse is tied to a subject
    subject = relationship("Subject", back_populates="timecourses")
    
    # Each timecourse is also tied to a study
    study = relationship("Study", back_populates="timecourses")

    # Many-to-many self-referencing relationship for data lineage (DAG)
    derived_from = relationship(
        "Timecourse",
        secondary=timecourse_lineage_association,
        primaryjoin=id == timecourse_lineage_association.c.derived_timecourse_id,
        secondaryjoin=id == timecourse_lineage_association.c.parent_timecourse_id,
        back_populates="derived_timecourses",
        lazy='dynamic'
    )

    derived_timecourses = relationship(
        "Timecourse",
        secondary=timecourse_lineage_association,
        primaryjoin=id == timecourse_lineage_association.c.parent_timecourse_id,
        secondaryjoin=id == timecourse_lineage_association.c.derived_timecourse_id,
        back_populates="derived_from",
        lazy='dynamic'
    )
