import numpy as np
from typing import Dict, Generic, List, Union, TypeVar, Type, Tuple
from abc import ABC, abstractmethod
import soundfile as sf
import mne
import pandas as pd
import cv2

from ..models import DataType, Timecourse


# pytype: disable=*
TimecoursePayload = Union[mne.io.Raw, Dict[str, np.ndarray],
                         pd.DataFrame, np.ndarray]
                          
TYPE_TO_EXTENSION = {}
TYPE_TO_SERIALIZER: Dict[Tuple[DataType, type], Type['PayloadSerializer[TimecoursePayload]']] = {}


EXTENSION_TO_TYPE = {v: k[1] for k, v in TYPE_TO_EXTENSION.items()}

# pytype: enable=*


T = TypeVar('T', bound=TimecoursePayload)
class PayloadSerializer(ABC, Generic[T]):

  extension: str

  @abstractmethod
  def _write_to_file(self, payload: T, fname: str):
    raise NotImplementedError

  def to_file(self, fname: str, payload: T):
    ext = fname.split('.')[-1]
    # if not isinstance(payload, self.data_type):
    #   raise ValueError(f"{self.__class__.__name__} must take payloads "
    #                    f"be of type {self.data_type}, but was given "
    #                    f"{type(payload)}.")
    if not fname.endswith(self.extension):
      raise ValueError(f"File name must have extension {self.extension} "
                       f"but was given {ext}.")
    self._write_to_file(payload, fname)
  
  @abstractmethod
  def _read_from_file(self, fname: str) -> T:
    raise NotImplementedError

  def from_file(self, fname) -> T:
    ext = fname.split('.')[-1]
    if not fname.endswith(self.extension):
      raise ValueError(f"File name must have extension {self.extension} "
                       f"but was given {ext}.")
    return self._read_from_file(fname)
  
  @classmethod
  def register(cls, data_types: List[DataType]):
    from typing import get_type_hints
    
    # Get the concrete type from the write method's type hints
    hints = get_type_hints(cls._write_to_file)
    concrete_type = hints['payload']
    if hasattr(concrete_type, "__origin__"):
        concrete_type = concrete_type.__args__[0]
      
    for data_type in data_types:
      TYPE_TO_EXTENSION[(data_type, concrete_type)] = cls.extension
      EXTENSION_TO_TYPE[cls.extension] = (data_type, concrete_type)
      TYPE_TO_SERIALIZER[(data_type, concrete_type)] = cls

class NumpyPayloadSerializer(PayloadSerializer[np.ndarray]):
  extension = "npz"

  def _write_to_file(self, payload: np.ndarray, fname: str):
    np.savez(fname, payload)

  def _read_from_file(self, fname: str) -> np.ndarray:
    return np.load(fname)

NumpyPayloadSerializer.register([DataType.FMRI])
  

class DataFramePayloadSerializer(PayloadSerializer[pd.DataFrame]):
  extension = "parquet"

  def _write_to_file(self, payload: pd.DataFrame, fname: str):
    payload.to_parquet(fname, index=False)

  def _read_from_file(self, fname: str) -> pd.DataFrame:
    return pd.read_parquet(fname)

DataFramePayloadSerializer.register([DataType.INPUT_RESPONSE])

class EEGPayloadSerializer(PayloadSerializer[mne.io.Raw]):
  extension = "fif"

  def _write_to_file(self, payload: mne.io.Raw, fname: str):
    payload.save(fname, overwrite=True)

  def _read_from_file(self, fname: str) -> mne.io.Raw:
    return mne.io.read_raw_fif(fname, preload=True)

EEGPayloadSerializer.register([DataType.EEG])

class VideoPayloadSerializer(PayloadSerializer[np.ndarray]):
  extension = "mp4"

  def _write_to_file(self, payload: np.ndarray, fname: str):
    # Expects payload to be a numpy array of shape (frames, height, width, channels)
    # with dtype uint8 and values in [0, 255]
    if len(payload.shape) != 4:
      raise ValueError(f"Video payload must have 4 dimensions but got {len(payload.shape)}")
    if payload.dtype != np.uint8:
      raise ValueError(f"Video payload must have dtype uint8 but got {payload.dtype}")
    
    # Get video dimensions
    n_frames, height, width, channels = payload.shape
    if channels != 3:
      raise ValueError(f"Video payload must have 3 channels but got {channels}")
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(fname, fourcc, 30.0, (width, height))
    
    try:
      # Write each frame
      for frame in payload:
        # OpenCV expects BGR format
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
    finally:
      out.release()

  def _read_from_file(self, fname: str) -> np.ndarray:
    # Open video file
    cap = cv2.VideoCapture(fname)
    
    try:
      # Get video properties
      frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
      height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
      width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
      
      # Initialize array to store frames
      frames = np.empty((frame_count, height, width, 3), dtype=np.uint8)
      
      # Read all frames
      for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
          raise ValueError(f"Failed to read frame {i} from video file")
        # Convert BGR to RGB
        frames[i] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
      return frames
      
    finally:
      cap.release()

VideoPayloadSerializer.register([DataType.VIDEO, DataType.VISUAL_PROMPT])

class AudioPayloadSerializer(PayloadSerializer[np.ndarray]):
  extension = "mp3"

  def _write_to_file(self, payload: np.ndarray, fname: str):
    # Validate payload dimensions and type
    if len(payload.shape) != 2:
      raise ValueError(f"Audio payload must have 2 dimensions but got {len(payload.shape)}")
    if payload.dtype != np.float32:
      raise ValueError(f"Audio payload must have dtype float32 but got {payload.dtype}")
    
    # Get audio properties
    samples, channels = payload.shape
    if channels > 2:
      raise ValueError(f"Audio payload must have 1 or 2 channels but got {channels}")
    
    # Scale to int16 range and convert
    scaled = np.clip(payload * 32768.0, -32768, 32767)
    samples_int16 = scaled.astype(np.int16)
    
    # Write MP3 file
    sf.write(fname, samples_int16, 44100, format='mp3')

  def _read_from_file(self, fname: str) -> np.ndarray:
    # Read audio file
    samples, sr = sf.read(fname)
    
    # Convert to float32 in [-1, 1] range
    samples_float = samples.astype(np.float32)
    if samples_float.ndim == 1:
      samples_float = samples_float.reshape(-1, 1)
    
    return samples_float / 32768.0

AudioPayloadSerializer.register([DataType.AUDITORY_PROMPT])


class FMRIPayloadSerializer(PayloadSerializer[np.ndarray]):
    extension = "npz"

    def _write_to_file(self, payload: np.ndarray, fname: str):
        # Validate payload dimensions
        if len(payload.shape) < 3:
            raise ValueError(f"FMRI payload must have at least 3 dimensions but got {len(payload.shape)}")
        
        # Save as compressed npz file
        np.savez_compressed(fname, data=payload)

    def _read_from_file(self, fname: str) -> np.ndarray:
        # Load npz file
        with np.load(fname) as data:
            return data['data']

FMRIPayloadSerializer.register([DataType.FMRI])
