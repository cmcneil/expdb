from typing import Type
from abc import ABC, abstractmethod

from . import format as fmt
from ..models import DataType, Timecourse


import os
import re
import subprocess
import tempfile


class StorageManager(ABC):
  def __init__(self, local_cache_dir=None):
    """Initialize a StorageManager object.

    StorageManager objects are responsible for storing and retrieving data
    associated with Timecourse objects. They manage the storage backend,
    whether it is local or remote, as well as caching logic. They handle
    serialization and deserialization of data through the fmt module.

    Args:
        local_cache_dir (str, optional): If set, this StorageManager will cache
            data locally at this directory. Otherwise, it will download data
            from the URI specified in the Timecourse each time it is accessed.
    """
    
    self.local_cache_dir = local_cache_dir

  def store(self, timecourse: Timecourse, payload: fmt.TimecoursePayload):
    """Store a timecourse payload in the storage backend.

    Args:
        timecourse (Timecourse): The timecourse object containing metadata
        payload (TimecoursePayload): The data payload to store

    The data will be serialized using the appropriate serializer for the data type
    and stored either directly or through the local cache depending on configuration.
    """
    data_type = timecourse.data.type
    serializer = fmt.TYPE_TO_SERIALIZER[(data_type, type(payload))]()
    path = self._get_local_path_from_data(timecourse, type(payload))
    uri = timecourse.path

    if self.local_cache_dir is not None:
      local_path = os.path.join(self.local_cache_dir, path)
      os.makedirs(os.path.dirname(local_path), exist_ok=True)
      serializer.to_file(local_path, payload)
      self._upload_data_to_uri(local_path, uri)
    else:
      with tempfile.NamedTemporaryFile(
        suffix=f".{fmt.TYPE_TO_EXTENSION[data_type, type(payload)]}") as tf:
        serializer.to_file(tf.name, payload)
        try:
          self._upload_data_to_uri(tf.name, uri)
        finally:
          tf.close()

  def retrieve(self, timecourse: Timecourse) -> fmt.TimecoursePayload:
    """Retrieve a timecourse payload from storage.

    Args:
        timecourse (Timecourse): The timecourse object containing metadata and path

    Returns:
        TimecoursePayload: The deserialized data payload

    The data will be retrieved either from local cache if available or downloaded
    from the storage backend.
    """
    uri = timecourse.path
    ext = uri.split('.')[-1]
    data_type, filetype = fmt.EXTENSION_TO_TYPE[ext]
    serializer = fmt.TYPE_TO_SERIALIZER[(data_type, filetype)]()

    if self.local_cache_dir is not None:
      local_path = os.path.join(
        self.local_cache_dir,
        self._get_local_path_from_data(timecourse, filetype))
      if not os.path.exists(local_path):
        self._download_data_from_uri(uri, local_path)
      payload = serializer.from_file(local_path)

    else:
      tf = tempfile.NamedTemporaryFile(suffix=f".{ext}")
      local_path = tf.name
      self._download_data_from_uri(uri, local_path)
      payload = serializer.from_file(local_path)
      tf.close()
    return payload

  def _get_local_path_from_data(self, timecourse: Timecourse,
                                payload_type: Type[fmt.TimecoursePayload]
                                ) -> str:
    """Generate a local filesystem path for storing the timecourse data.

    Args:
        timecourse (Timecourse): The timecourse object containing metadata
        payload_type (Type[TimecoursePayload]): The type of payload being stored

    Returns:
        str: The canonical path to the data
    """
    ext = fmt.TYPE_TO_EXTENSION[(timecourse.data.type, payload_type)]
    path = (f"{timecourse.study.name}/"
            f"{timecourse.subject.code}/{timecourse.data.modality.value}/"
            f"{timecourse.data.type.value}/"
            f"{timecourse.date_collected.strftime('%Y%m%d_%H%M%S')}.{ext}")
    return path
  
  @abstractmethod
  def get_uri_from_data(self, timecourse: Timecourse,
                        payload: fmt.TimecoursePayload) -> str:
    """Generate a URI for storing the timecourse data in the storage backend."""
    raise NotImplementedError

  @abstractmethod
  def _upload_data_to_uri(self, fname: str, uri: str):
    """Upload a local file to the storage backend."""
    raise NotImplementedError

  @abstractmethod
  def _download_data_from_uri(self, path: str, local_path: str):
    """Download a file from the storage backend to a local path."""
    raise NotImplementedError

  
class GCSStorageManager(StorageManager):
  """Storage manager implementation for Google Cloud Storage.

  This class implements the StorageManager interface for storing and retrieving files
  from Google Cloud Storage (GCS) buckets. It uses the gcloud CLI tool for file operations.

  Args:
    gcs_bucket: The GCS bucket URL in the format "gs://bucket_name/"
    local_cache_dir: Optional local directory to cache downloaded files

  Raises:
    ValueError: If the gcs_bucket URL format is invalid
  """
  def __init__(self, gcs_bucket, local_cache_dir=None):
    super().__init__(local_cache_dir=local_cache_dir)

    pattern =re.compile(r"(gs:\/\/[a-zA-Z0-9_-]+)\/?")
    m = re.match(pattern, gcs_bucket)
    if m is None:
      raise ValueError(f"Invalid GCS bucket Format: {gcs_bucket}, "
                       "expected gs://bucket_name/")
    self.gcs_prefix = m.group(1)
  
  def get_uri_from_data(self, timecourse: Timecourse,
                        payload: fmt.TimecoursePayload) -> str:
    local_path = self._get_local_path_from_data(timecourse, type(payload))
    return f"{self.gcs_prefix}/{local_path}"
  
  def _upload_data_to_uri(self, fname: str, uri: str):
    try:
        subprocess.run(
            ["gcloud", "storage", "cp", fname, uri],
            check=True  # Raises CalledProcessError on failure
        )
        print(f"File uploaded to: {uri}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to upload file: {e}")

  def _download_data_from_uri(self, path: str, local_path: str):
    try:
        subprocess.run(
            ["gcloud", "storage", "cp", path, local_path],
            check=True  # Raises CalledProcessError on failure
        )
        print(f"File downloaded to: {local_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download file: {e}")


class LocalStorageManager(StorageManager):
  """Storage manager implementation for local filesystem storage.

  This class implements the StorageManager interface for storing and retrieving files
  from the local filesystem.

  Args:
    file_root: The root directory for storing files
  """
  def __init__(self, file_root: str):
    super().__init__(local_cache_dir=file_root)
  
  def get_uri_from_data(self, timecourse: Timecourse,
                        payload: fmt.TimecoursePayload) -> str:
    return self._get_local_path_from_data(timecourse, type(payload))

  def _upload_data_to_uri(self, fname: str, uri: str):
    pass

  def _download_data_from_uri(self, path: str, local_path: str):
    pass