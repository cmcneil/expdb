from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

import sqlalchemy.orm
from sqlalchemy import text
from sqlalchemy.orm import object_session

from abc import ABC, abstractmethod
from datetime import datetime
import json

from ..config import get_config
from ..db import Session
from ..models import Data, Study, Subject, Timecourse,TransformData
from ..storage import StorageManager, GCSStorageManager
from ..utils import data_utils as du
from ..utils import git_utils

CONFIG = get_config()


T = TypeVar('T',  bound=du.TimecoursePayload)
U = TypeVar('U',  bound=du.TimecoursePayload)

# Custom JSON Encoder that looks for __json__
class CustomParamsEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__json__"):
            return obj.__json__()
        return super().default(obj)


class Transform(ABC, Generic[T, U]):
    input_datatype: Data
    output_datatype: Data

    def __init__(self, timecourse: Optional[Timecourse],
                 session: Optional[sqlalchemy.orm.Session],
                 storage_manager: Optional[StorageManager] = None,
                 **params):
        self.params = params
        self.data = None
        sess = None
        self.input_timecourses = []
        if storage_manager is None:
            self.storage_manager = GCSStorageManager(
                CONFIG.GCS_BUCKET,
                local_cache_dir=CONFIG.LOCAL_CACHE_DIR
            )
        else:
            self.storage_manager = storage_manager
        
        if timecourse is not None:
            if timecourse.data != self.input_datatype:
                raise ValueError("Timecourse data type does not match input "
                                 "data type.")
            self.session = object_session(timecourse)
            self.input_timecourses.append(timecourse)
        elif session is not None:
            self.session = session
        else:
            self.session = Session()


    @abstractmethod
    def transform(self, data: T) -> U:
        raise NotImplementedError
    
    def _transform_names(self) -> List[str]:
        return [self.__class__.__name__]
    
    def _transform_params(self) -> List[Dict[str, Any]]:
        return [self.params]
    
    def _get_transform_data(self) -> TransformData:
        if not (CONFIG.DEBUG or git_utils.no_uncommitted_changes()):
            raise Exception("Git repo has uncommitted changes.")
        transform_data = TransformData(
            transform_names_json=json.dumps(self._transform_names(),
                                            cls=CustomParamsEncoder),
            transform_params_json=json.dumps(self._transform_params(),
                                             cls=CustomParamsEncoder),
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
            date_collected = datetime.now().astimezone()

        )
        for parent in self.input_timecourses:
            new_timecourse.derived_from.append(parent)
        
        # Get the upload path for the new timecourse
        uri = self.storage_manager.get_uri_from_data(new_timecourse, T)
        # gs_url = du.construct_gs_url(new_timecourse)
        new_timecourse.path = uri
        return new_timecourse
        

    def _load_data(self):
        self.data = []
        for tc in self.input_timecourses:
            self.data.append(self.storage_manager.retrieve(tc))
        
    def commit(self):
        # du.reupload_data_to_gcs(self.out_data,
        #                         self.new_timecourse.path)
        self.storage_manager.store(self.new_timecourse, self.out_data)
        self.session.add(self.new_timecourse)
        self.session.commit()
        

W = TypeVar('W', bound=du.TimecoursePayload)
class RawDataUpload(Transform[W, W], Generic[W]):
    
    def __init__(self, data_type: Data, subject: Subject, study: Study,
                 is_pilot: bool, file_path: str,
                 date_collected: Optional[datetime] = None,
                 storage_manager: Optional[StorageManager] = None):    
        super().__init__(None, session=object_session(study),
                         storage_manager=storage_manager)
        self.output_datatype = data_type
        self.date_collected = date_collected
        self.file_path = file_path
        self.study = study
        self.subject = subject
        self.is_pilot = is_pilot

    def _construct_new_timecourse(self):
        # Get an ID for the timecourse.
        result = self.session.execute(
            text("SELECT nextval('timecourses_id_seq')"))
        next_id = result.scalar()

        if self.date_collected is None:
            print("DEBUG: No date collected")
            self.date_collected = datetime.now().astimezone()

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

    def transform(self, data: W) -> W:
        return data