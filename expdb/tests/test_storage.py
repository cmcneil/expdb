import pytest
import os
import tempfile
import numpy as np
from datetime import datetime
from unittest.mock import patch
from ..storage import GCSStorageManager, LocalStorageManager
from ..models import Data, DataType, Modality, Timecourse, Study, Subject
from ..storage import format as fmt


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

@pytest.fixture
def real_timecourse():
    # Create a real Timecourse instance with realistic attributes
    study = Study(name="study_name", github_repo="test/repo")
    subject = Subject(name="Testy McTesterson", code="TT",
                      age=20, meditation_experience=5)
    return Timecourse(
        path="gs://bucket_name/path/to/file.npy",
        data=Data(type=DataType.FMRI, modality=Modality.IMAGING, sampling_rate=1.0),
        date_collected=datetime(2024, 1, 1, 12, 0, 0),
        subject=subject,
        study=study
    )

@pytest.fixture
def ndarray_payload():
    # Create a real np.ndarray payload as test data
    return np.random.rand(10, 10, 10)

@pytest.fixture
def gcs_storage_manager():
    return GCSStorageManager(gcs_bucket="gs://bucket_name")

@pytest.fixture
def cache_dir():
    return tempfile.TemporaryDirectory().name

@pytest.fixture
def local_storage_manager(cache_dir):
    return LocalStorageManager(file_root=cache_dir)

@patch("subprocess.run")
def test_upload_data_to_uri_gcs(mock_subprocess, gcs_storage_manager):
    gcs_storage_manager._upload_data_to_uri("local_file", "gs://bucket_name/path")
    mock_subprocess.assert_called_once_with(
        ["gcloud", "storage", "cp", "local_file", "gs://bucket_name/path"],
        check=True
    )

@patch("subprocess.run")
def test_download_data_from_uri_gcs(mock_subprocess, gcs_storage_manager):
    gcs_storage_manager._download_data_from_uri("gs://bucket_name/path", "local_path")
    mock_subprocess.assert_called_once_with(
        ["gcloud", "storage", "cp", "gs://bucket_name/path", "local_path"],
        check=True
    )

def test_store_retrieve_with_ndarray_payload(local_storage_manager,
                                             real_timecourse, ndarray_payload):
    # Retrieve the actual serializer for np.ndarray
    serializer = fmt.TYPE_TO_SERIALIZER[(DataType.FMRI, np.ndarray)]()

    uri = local_storage_manager.get_uri_from_data(
        real_timecourse, ndarray_payload)
    real_timecourse.path = uri

    # Store the payload, which should use the local cache
    local_storage_manager.store(real_timecourse, ndarray_payload)

    # Check that the payload was written to the expected local path
    local_path = os.path.join(local_storage_manager.local_cache_dir, 
                              uri)
    assert os.path.exists(local_path)

    payload2 = local_storage_manager.retrieve(real_timecourse)
    # Clean up the created file after the test
    np.testing.assert_array_equal(payload2, ndarray_payload)  # check that the payload matches payload2
    os.remove(local_path)

# def test_retrieve_with_ndarray_payload(local_storage_manager, real_timecourse, ndarray_payload):
#     # Retrieve the actual serializer for np.ndarray
#     serializer = fmt.TYPE_TO_SERIALIZER[("np_array", np.ndarray)]()

#     # Manually write the payload to the expected local path for the test
#     local_path = os.path.join(local_storage_manager.local_cache_dir, 
#                               local_storage_manager._get_local_path_from_data(real_timecourse, np.ndarray))
#     os.makedirs(os.path.dirname(local_path), exist_ok=True)
#     serializer.to_file(local_path, ndarray_payload)

#     # Retrieve the payload and check it matches the original ndarray
#     retrieved_payload = local_storage_manager.retrieve(real_timecourse)
#     np.testing.assert_array_equal(retrieved_payload, ndarray_payload)

#     # Clean up the created file after the test
#     os.remove(local_path)
