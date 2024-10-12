from typing import List, Optional, Type

from sqlalchemy import Column, Enum, Float, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import composite, relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

import dataclasses
import enum
import json

from . import Base, Study, Subject  # Import the Base model
from ..transforms import Transform


class Modality(enum.Enum):
    UNKNOWN = "UNKNOWN"
    # STIMULUS is a timecourse of stimulus data presented to the subject. This
    # could be video, a record of events, questions passed to them, etc.
    STIMULUS = "STIMULUS"
    # BEHAVIORAL is a timecourse of the subject's behavioral response,
    # such as button presses, task performance, etc.
    BEHAVIORAL = "BEHAVIORAL"
    # IMAGING is a timecourse of the subject's brain data, such as EEG or MEG.
    IMAGING = "IMAGING"


class DataType(enum.Enum):
    UNKNOWN = "UNKNOWN"
    EEG = "EEG"
    FMRI = "FMRI"
    INPUT_RESPONSE = "INPUT_RESPONSE"
    VISUAL_PROMPT = "VISUAL_PROMPT"
    VIDEO = "VIDEO"
    AUDITORY_PROMPT = "AUDITORY_PROMPT"


@dataclasses.dataclass
class Data:
    """
    A Data object.

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
    sampling_rate: float
    path: str
    modality: Modality = Modality.UNKNOWN
    type: DataType = DataType.UNKNOWN
    description: str = ""

    def __post_init__(self):
        # Validate that the provided modality is a valid enum value
        if not isinstance(self.modality, Modality):
            raise ValueError(f"Invalid modality: {self.modality}")
        
        # Validate that the provided type is a valid enum value
        if not isinstance(self.type, DataType):
            raise ValueError(f"Invalid type: {self.type}")

    def __repr__(self) -> str:
        return (f"Data({self.type}, {self.modality}, "
                f"{self.sampling_rate}, {self.path}, {self.description})")

class TransformData:
    """An object describing how a timecourse was created.
    
    Parameters
    ----------
    transform_names_json: str
        A JSON string of the transform names, which are the names of the
        transform classes used to create the timecourse. Should not be used by
        the user, only SQLAlchemy.
    transform_params_json: str
        A JSON string of the transform parameters, which are the parameters
        used to create the timecourse.
    git_commit: str
        The git commit of the code used to produce the timecourse.
    # """
    # transform_classes: List[Transform] = dataclasses.field(
    #     default_factory=list, repr=False)  # Not persisted
    def __init__(self, transform_names_json: str,
                 transform_params_json: str, git_commit: str):
        self.transform_names_json = transform_names_json
        self.transform_params_json = transform_params_json
        self.git_commit = git_commit
        self._validate()
    # transform_names_json: str = ""
    # transform_params_json: str = ""
    # git_commit: str = ""

    def __composite_values__(self):
        return (
            self.transform_names_json,
            self.transform_params_json,
            self.git_commit
        )
    
    def __eq__(self, other):
        """Define equality between composite objects."""
        if not isinstance(other, TransformData):
            return False
        return (self.transform_names_json == other.transform_names_json and
                self.transform_params_json == other.transform_params_json and
                self.git_commit == other.git_commit)

    def _validate(self):
        # Validate that the length of names and params match
        transform_names = json.loads(self.transform_names_json)
        transform_params = json.loads(self.transform_params_json)

        if len(transform_names) != len(transform_params):
            raise ValueError(
                f"Transform names and params must have the same length: "
                f"{len(transform_names)} != {len(transform_params)}"
            )

        # Optionally validate the classes are in the correct namespace or subclass of `Transform`
        # for cls in self.transform_classes:
        #     if not issubclass(cls, Transform):
        #         raise ValueError(f"{cls} is not a valid subclass of Transform")
        # def __post_init__(self):
    #     transform_names = json.loads(self.transform_names_json)
    #     transform_params = json.loads(self.transform_params_json)

    #     if len(transform_names) != len(transform_params):
    #         raise ValueError(
    #             f"Transform names and params must have the same length: "
    #             f"{len(transform_names)} != {len(transform_params)}")

    #     are_classes_in_namespace  = {name: is_class_in_namespace(name)
    #                                  for name in transform_names}
    #     are_classes_xfm  = {name: is_class_subclass(name, Transform)
    #                         for name in transform_names}
    #     if not all(are_classes_in_namespace.values()):
    #         raise ValueError(
    #             f"Invalid transform names: "
    #             f"{[k for k, v in are_classes_in_namespace.items() if not v]}")
    #     if not all(are_classes_xfm.values()):
    #         raise ValueError(
    #             f"Invalid transform classes: "
    #             f"{[k for k, v in are_classes_xfm.items() if not v]}")
    # @validates('transform_names_json')
    # def validate_transform_names(self, key, value):
    #     # Ensure valid JSON for names and params
    #     json.loads(value)
    #     return value

    # @validates('transform_params_json')
    # def validate_transform_params(self, key, value):
    #     # Ensure valid JSON for params
    #     json.loads(value)
    #     return value


    def __repr__(self) -> str:
        return (f"Transform({'->'.join(self.transform_names)},"
                f"#{self.git_commit})")



# Association table for Timecourse DAG (many-to-many self-referencing)
timecourse_lineage_association = Table(
    'timecourse_lineage_association',
    Base.metadata,
    Column('derived_timecourse_id', ForeignKey('timecourses.id'),
           primary_key=True),
    Column('parent_timecourse_id', ForeignKey('timecourses.id'),
            primary_key=True)
)


class Timecourse(Base):
    __tablename__ = 'timecourses'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[Data] = composite(Data,
                                   mapped_column("sampling_rate", Float,
                                                 nullable=False),
                                   mapped_column("path", String,
                                                 nullable=False),
                                   mapped_column("modality", Enum(Modality),
                                                 nullable=False),
                                   mapped_column("type", Enum(DataType),
                                                 nullable=False),
                                   mapped_column("description", String,
                                                 nullable=True))

    transform: Mapped[TransformData] = composite(
        TransformData,
        mapped_column("transform_names_json", String, nullable=False),
        mapped_column("transform_params_json", String, nullable=False),
        mapped_column("git_commit", String, nullable=False))

    # Timestamp when the timecourse was created
    date_collected: Mapped[DateTime] = mapped_column(DateTime,
                                                     server_default=func.now())
    # Boolean flag that will propagate to related timecourses
    # Marks whether the data is pilot data.
    _is_pilot: Mapped[bool] = mapped_column(default=False)

    @hybrid_property
    def is_pilot(self) -> bool:
        return self._is_pilot
    
    @is_pilot.setter
    def is_pilot(self, value: bool):
        self._is_pilot = value
        self.propagate_is_pilot(value)
    
    # Each timecourse is tied to a subject
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.id'), 
                                            nullable=False)
    subject: Mapped["Subject"] = relationship("Subject",
                                              back_populates="timecourses")
    
    # Each timecourse is also tied to a study
    study_id: Mapped[int] = mapped_column(ForeignKey('studies.id'), 
                                          nullable=False)
    study: Mapped["Study"] = relationship("Study", back_populates="timecourses")

    # Many-to-many self-referencing relationship for data lineage (DAG)
    derived_from: Mapped[List["Timecourse"]] = relationship(
        "Timecourse",
        secondary=timecourse_lineage_association,
        primaryjoin=id == timecourse_lineage_association.c.derived_timecourse_id,
        secondaryjoin=id == timecourse_lineage_association.c.parent_timecourse_id,
        back_populates="derived_timecourses",
        lazy='dynamic'
    )

    derived_timecourses: Mapped[List["Timecourse"]] = relationship(
        "Timecourse",
        secondary=timecourse_lineage_association,
        primaryjoin=id == timecourse_lineage_association.c.parent_timecourse_id,
        secondaryjoin=id == timecourse_lineage_association.c.derived_timecourse_id,
        back_populates="derived_from",
        lazy='dynamic'
    )

    def propagate_is_pilot(self, value: bool):
        """
        Recursively propagate the is_pilot flag to both parent (derived_from) 
        and child (derived_timecourses) timecourses.
        """
        # Propagate to all derived (child) timecourses
        for child_timecourse in self.derived_timecourses:
            if child_timecourse.is_pilot != value:
                child_timecourse.is_pilot = value

        # Propagate to all parent timecourses
        for parent_timecourse in self.derived_from:
            if parent_timecourse.is_pilot != value:
                parent_timecourse.is_pilot = value


