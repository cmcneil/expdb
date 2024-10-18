from ..transforms import RawDataUpload
from ..config import get_config
from ..db import Session
from ..models import Data, DataType, Modality, Timecourse, TransformData, Subject, Study
import json
import os

def upload_raw_timecourse(sess, data: Data, subject_code: str, study_name: str,
                          is_pilot: bool, file_path: str,
                          date_collected: Optional[datetime] = None):
  
  raw_upload_xfm = RawDataUpload()