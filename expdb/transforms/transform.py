from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import object_session

from abc import ABC, abstractmethod
from datetime import datetime
import json

from ..config import get_config
from ..db import Session
from ..models import Data, Study, Subject, Timecourse,TransformData
from ..utils import data_utils as du
from ..utils import git_utils

CONFIG = get_config()


class Transform(ABC):
    input_datatype: Data
    output_datatype: Data

    def __init__(self, timecourse: Timecourse, **params: Dict[str, Any]):
        self.params = params
        self.data = None
        sess = None
        
        if timecourse is not None:
            sess = object_session(timecourse)

        if sess:
            self.session = sess
            self.input_timecourse = timecourse
        else:
            self.session = Session()
            self.input_timecourse = self.session.merge(timecourse)

    @abstractmethod
    def transform(self, data) -> Any:
        raise NotImplementedError
    
    def _transform_names(self) -> List[str]:
        return [self.__class__.__name__]
    
    def _transform_params(self) -> List[Dict[str, Any]]:
        return [self.params]
    
    def _get_transform_data(self) -> TransformData:
        if not (CONFIG.DEBUG or git_utils.no_uncommitted_changes()):
            raise Exception("Git repo has uncommitted changes.")
        transform_data = TransformData(
            transform_names_json=json.dumps(self._transform_names()),
            transform_params_json=json.dumps(self._transform_params()),
            git_commit=git_utils.get_most_recent_commit()
        )
        return transform_data
    
    def apply_transform(self):
        self._load_data()
        self.out_data = self.transform(self.data)
        new_timecourse = self._construct_new_timecourse()
        self.new_timecourse = new_timecourse

    def _construct_new_timecourse(self):
        # Get an ID for the timecourse.
        result = self.session.execute(
            text("SELECT nextval('timecourse_id_seq')"))
        next_id = result.scalar()

        transform_data = self._get_transform_data()
        new_timecourse = Timecourse(
            id=next_id,
            study=self.input_timecourses[0].study,
            subject=self.input_timecourses[0].subject,
            data=self.output_datatype,
            transform=transform_data,
            is_pilot=self.input_timecourses[0].is_pilot,
            date_collected = datetime.now.astimezone()

        )
        for parent in self.input_timecourses:
            new_timecourse.derived_from.append(parent)
        
        # Get the upload path for the new timecourse
        gs_url = du.construct_gs_url(new_timecourse)
        new_timecourse.path = gs_url
        return new_timecourse
        

    def _load_data(self):
        path = self.timecourse.path
        self.data = du.load_data(path)
        
    def commit(self):
        du.reupload_data_to_gcs(self.out_data,
                                self.new_timecourse.path)
        self.session.add(self.new_timecourse)
        self.session.commit()
        

class RawDataUpload(Transform):
    
    def __init__(self, data_type: Data, subject_code: str, study_name: str,
                 is_pilot: bool, file_path: str,
                 date_collected: Optional[datetime.Datetime] = None):         
        super().__init__(None, data_type=data_type, subject_code=subject_code,
                         study_name=study_name, is_pilot=is_pilot,
                         date_collected=date_collected, file_path=file_path)
        self.output_datatype = data_type
        self.date_collected = date_collected
        self.file_path = file_path
        self.subject = self.session.query(Subject).filter_by(code=subject_code
                                                        ).one_or_none()
        self.study = self.session.query(Study).filter_by(name=study_name
                                                    ).one_or_none()

        self.is_pilot = is_pilot
        if self.subject is None:
            raise ValueError(f"Subject with code '{subject_code}' does not exist.")
        if self.study is None:
            raise ValueError(f"Study with name '{study_name}' does not exist.")

    def _construct_new_timecourse(self):
        # Get an ID for the timecourse.
        result = self.session.execute(
            text("SELECT nextval('timecourse_id_seq')"))
        next_id = result.scalar()

        if self.date_collected is None:
            self.date_collected = datetime.now.astimezone()

        new_timecourse = Timecourse(
            id=next_id,
            study=self.study,
            subject=self.subject,
            data=self.output_datatype,
            transform=self._get_transform_data(),
            is_pilot=self.is_pilot,
            date_collected = self.date_collected
        )
        # Get the upload path for the new timecourse
        gs_url = du.construct_gs_url(new_timecourse)
        new_timecourse.path = gs_url
        return new_timecourse

    def _load_data(self):
        self.data = du.load_data_from_local(self.file_path)

    def transform(self, data) -> Any:
        return data