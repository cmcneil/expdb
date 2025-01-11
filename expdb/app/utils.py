from typing import Optional
from datetime import datetime

from ..transforms import RawDataUpload
from ..config import get_config
from ..db import Session
from ..models import Data, DataType, Modality, Timecourse, TransformData, Subject, Study
import json
import os

def upload_raw_timecourse(sess, data: Data, subject_code: str, study_name: str,
                          is_pilot: bool, file_path: str,
                          date_collected: Optional[datetime] = None):
    
    # Check if study exists in DB
    study = sess.query(Study).filter(Study.name == study_name).first()
    if study is None:
        raise ValueError(f"Study '{study_name}' not found in database")
        
    # Check if subject exists in DB
    subject = sess.query(Subject).filter(Subject.code == subject_code).first()
    if subject is None:
        raise ValueError(f"Subject '{subject_code}' not found in database")

    # Create and execute upload transform
    raw_upload_xfm = RawDataUpload(
        data_type=data,
        subject=subject,
        study=study, 
        is_pilot=is_pilot,
        file_path=file_path,
        date_collected=date_collected if date_collected is not None else datetime.now()
    )
    raw_upload_xfm.apply_transform()
    raw_upload_xfm.commit()