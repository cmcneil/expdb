from typing import Generic, List, Union, Type, TypeVar
from abc import ABCMeta, abstractmethod

import mne
import numpy as np
import pandas as pd

from ..models import DataType, Timecourse


TYPE_TO_EXTENSION = {
  (DataType.EEG, mne.io.Raw): "fif",
  # (DataType.FMRI, np.ndarray): "npz",
  (DataType.INPUT_RESPONSE, pd.DataFrame): "parquet",
  (DataType.VISUAL_PROMPT, np.ndarray): "mp4", 
  (DataType.AUDITORY_PROMPT, np.ndarray): "mp3",
  (DataType.VIDEO, np.ndarray): "mp4",
}

TYPE_TO_SERIALIZER = {
  (DataType.EEG, mne.io.Raw): EEGPayloadSerializer,
  # (DataType.FMRI, np.ndarray): NumpyPayloadSerializer,
  (DataType.INPUT_RESPONSE, pd.DataFrame): DataFramePayloadSerializer,
  (DataType.VISUAL_PROMPT, np.ndarray): VideoPayloadSerializer,
  (DataType.AUDITORY_PROMPT, np.ndarray): AudioPayloadSerializer,
  (DataType.VIDEO, np.ndarray): VideoPayloadSerializer,
}

EXTENSION_TO_TYPE = {v: k[1] for k, v in TYPE_TO_EXTENSION.items()}

TimecoursePayload = Union[mne.io.Raw, Dict[str, np.ndarray],
                          pd.DataFrame, np.ndarray]


T = TypeVar('T', bound=TimecoursePayload)
class PayloadSerializer(ABCMeta, Generic[T]):

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
    for data_type in data_types:
      TYPE_TO_EXTENSION[(data_type, T)] = cls.extension
      EXTENSION_TO_TYPE[cls.extension] = (data_type, T)
      TYPE_TO_SERIALIZER[(data_type, T)] = cls

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