from typing import Dict, Union

from ..config import get_config
from ..models import DataType, Timecourse

import io
import numpy as np
import pandas as pd
from google.cloud import storage
import mne
import cv2  # OpenCV for video
from pydub import AudioSegment


DATATYPE_TO_EXTENSION = {
    DataType.EEG: "bdf",
    DataType.FMRI: "npz",
    DataType.INPUT_RESPONSE: "parquet",
    DataType.VISUAL_PROMPT: "mp4",
    DataType.AUDITORY_PROMPT: "mp3",
    DataType.VIDEO: "mp4",
}

CONFIG = get_config()

def construct_gs_url(timecourse: Timecourse) -> str:
    """
    Constructs a Google Cloud Storage path from environment variables.
    
    Returns:
        str: Google Cloud Storage path.
    """
    ext = DATATYPE_TO_EXTENSION[timecourse.data_type]
    gs_path = (f"{CONFIG.GS_BUCKET_NAME}/{timecourse.study.name}/"
               f"{timecourse.subject.code}/{timecourse.data.modality}/"
               f"{timecourse.data.type}/"
               f"{timecourse.date_collected.strftime('%Y%m%d_%H%M%S')}.{ext}")
    return f"gs://{gs_path}"


def load_bdf(data_bytes: bytes) -> mne.io.BaseRaw:
    """
    Loads EEG data from a BDF file stored in memory as bytes.
    
    Args:
        data_bytes (bytes): BDF file content in bytes.
    
    Returns:
        mne.io.BaseRaw: The loaded EEG data.
    """
    with io.BytesIO(data_bytes) as bdf_file:
        raw = mne.io.read_raw_bdf(bdf_file, preload=True)
        return raw

def load_npz(data_bytes: bytes) -> Dict[str, np.ndarray]:
    """
    Loads a .npz file from memory as bytes and returns a dictionary of numpy arrays.
    
    Args:
        data_bytes (bytes): NPZ file content in bytes.
    
    Returns:
        Dict[str, np.ndarray]: Dictionary of numpy arrays.
    """
    with io.BytesIO(data_bytes) as npz_file:
        npz_data = np.load(npz_file, allow_pickle=True)
        return dict(npz_data)

def load_parquet(data_bytes: bytes) -> pd.DataFrame:
    """
    Loads a Parquet file from memory as bytes and returns a pandas DataFrame.
    
    Args:
        data_bytes (bytes): Parquet file content in bytes.
    
    Returns:
        pd.DataFrame: Loaded pandas DataFrame.
    """
    with io.BytesIO(data_bytes) as parquet_file:
        df = pd.read_parquet(parquet_file)
        return df

def load_video(data_bytes: bytes) -> np.ndarray:
    """
    Loads a video file from memory as bytes and returns the frames as 
    numpy arrays.
    
    Args:
        data_bytes (bytes): Video file content in bytes.
    
    Returns:
        np.ndarray: Array of video frames.
    """    
    with io.BytesIO(data_bytes) as video_file:
        # Open the video file using OpenCV
        video_file.seek(0)  # Make sure we're at the start of the file
        video_array = []
        # Write the video_file to a temporary file to process with OpenCV
        temp_video_file = '/tmp/temp_video.mp4'
        with open(temp_video_file, 'wb') as f:
            f.write(video_file.read())
        cap = cv2.VideoCapture(temp_video_file)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            video_array.append(frame)
        cap.release()
        return np.array(video_array)

# Helper function to load audio data
def load_audio(data_bytes):
    with io.BytesIO(data_bytes) as audio_file:
        audio_segment = AudioSegment.from_file(audio_file)
        samples = np.array(audio_segment.get_array_of_samples())
        return samples
    
def save_bdf(data: mne.io.BaseRaw) -> io.BytesIO:
    """
    Save EEG data to a .bdf file and return it as a byte stream.
    
    Args:
        data: EEG data to be saved.
    
    Returns:
        io.BytesIO: Byte stream containing the .bdf file content.
    """
    bytes_io = io.BytesIO()
    data.save(bytes_io, fmt='bdf')
    bytes_io.seek(0)  # Reset stream pointer
    return bytes_io

# Helper function to save numpy arrays to NPZ format
def save_npz(data: Dict[str, np.ndarray]) -> io.BytesIO:
    """
    Save a dictionary of numpy arrays to a .npz file and return it as a byte stream.
    
    Args:
        data: Dictionary of numpy arrays.
    
    Returns:
        io.BytesIO: Byte stream containing the .npz file content.
    """
    bytes_io = io.BytesIO()
    np.savez(bytes_io, **data)
    bytes_io.seek(0)  # Reset stream pointer
    return bytes_io

# Helper function to save pandas DataFrame to Parquet format
def save_parquet(data: pd.DataFrame) -> io.BytesIO:
    """
    Save a pandas DataFrame to a Parquet file and return it as a byte stream.
    
    Args:
        data: The pandas DataFrame to be saved.
    
    Returns:
        io.BytesIO: Byte stream containing the Parquet file content.
    """
    bytes_io = io.BytesIO()
    data.to_parquet(bytes_io)
    bytes_io.seek(0)  # Reset stream pointer
    return bytes_io

# Helper function to save video data as a video file
def save_video(data: np.ndarray, file_path: str) -> io.BytesIO:
    """
    Save a numpy array of video frames to a video file and return it as a byte stream.
    
    Args:
        data: Numpy array of video frames.
        file_path: Path indicating the type of video file (e.g., .mp4, .avi).
    
    Returns:
        io.BytesIO: Byte stream containing the video file content.
    """
    bytes_io = io.BytesIO()
    # Use a temporary video file since OpenCV can't write directly to a stream
    temp_file_path = '/tmp/temp_video.mp4'  # Example for .mp4, change as needed
    height, width, layers = data[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # For .mp4 format
    video_writer = cv2.VideoWriter(temp_file_path, fourcc, 30.0, (width, height))
    
    for frame in data:
        video_writer.write(frame)
    
    video_writer.release()

    # Read back the temporary file into the byte stream
    with open(temp_file_path, 'rb') as f:
        bytes_io.write(f.read())
    bytes_io.seek(0)  # Reset stream pointer
    return bytes_io

# Helper function to save audio data as an audio file
def save_audio(data: np.ndarray, file_path: str) -> io.BytesIO:
    """
    Save a numpy array of audio samples to an audio file and return it as a byte stream.
    
    Args:
        data: Numpy array of audio samples.
        file_path: Path indicating the type of audio file (e.g., .mp3, .wav).
    
    Returns:
        io.BytesIO: Byte stream containing the audio file content.
    """
    bytes_io = io.BytesIO()
    audio_segment = AudioSegment(
        data.tobytes(), 
        frame_rate=44100,  # Assuming a default sample rate; adjust if necessary
        sample_width=data.dtype.itemsize, 
        channels=1  # Assuming mono; adjust if necessary
    )
    if file_path.endswith('.mp3'):
        audio_segment.export(bytes_io, format="mp3")
    elif file_path.endswith('.wav'):
        audio_segment.export(bytes_io, format="wav")
    else:
        raise ValueError("Unsupported audio format")
    
    bytes_io.seek(0)  # Reset stream pointer
    return bytes_io
    

def bytes_to_data(data_bytes: bytes, ext: str) -> Union[mne.io.BaseRaw,
                                             Dict[str, np.ndarray],
                                             pd.DataFrame,
                                             np.ndarray]:
    
    # Determine the file type based on file extension
    if ext == "bdf":
        # Load EEG data from .bdf file
        eeg_data = load_bdf(data_bytes)
        return eeg_data
    elif ext == ".npz":
        # Load .npz file into a dictionary of numpy arrays
        npz_data = load_npz(data_bytes)
        return npz_data
    elif ext == ".parquet":
        # Load parquet file into pandas dataframe
        df = load_parquet(data_bytes)
        return df
    elif (ext == '.mp4' or
          ext == '.avi' or
          ext == '.mov'):
        # Load video file as numpy arrays (frames)
        video_data = load_video(data_bytes)
        return video_data
    elif (ext == '.mp3' or 
          ext == '.wav'):
        # Load audio file as numpy arrays (waveform)
        audio_data = load_audio(data_bytes)
        return audio_data
    else:
        raise ValueError("Unsupported file format")

def load_data_from_gcs(gs_path: str) -> Union[mne.io.BaseRaw,
                                              Dict[str, np.ndarray],
                                              pd.DataFrame,
                                              np.ndarray]:
    """
    Loads data from a Google Cloud Storage bucket, determines the file type, 
    and returns the data loaded into an appropriate data structure.

    Args:
        gs_path (str): Google Cloud Storage path (gs://bucket_name/blob_name).
    
    Returns:
        Union[mne.io.BaseRaw, Dict[str, np.ndarray], pd.DataFrame, np.ndarray]: 
        Loaded data, either EEG data, npz data, a DataFrame, or numpy array (for video/audio).
    """
    # Initialize Google Cloud Storage client
    storage_client = storage.Client()
    
    # Extract bucket and blob names from the `gs://` path
    if gs_path.startswith("gs://"):
        gs_path = gs_path[5:]
    bucket_name, blob_path = gs_path.split("/", 1)
    
    # Get bucket and blob objects
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    
    # Download file as bytes stream
    data_bytes = blob.download_as_bytes()
    
    return bytes_to_data(data_bytes, blob_path.split(".")[-1])

def load_data_from_local(path: str) -> Union[mne.io.BaseRaw,
                                              Dict[str, np.ndarray],
                                              pd.DataFrame,
                                              np.ndarray]:
    """
    Loads data from a local path, determines the file type, and returns the data
    loaded into an appropriate data structure.

    Args:
        path (str): Local path to the file.
    
    Returns:
        Union[mne.io.BaseRaw, Dict[str, np.ndarray], pd.DataFrame, np.ndarray]: 
        Loaded data, either EEG data, npz data, a DataFrame, or numpy array (for video/audio).
    """
    with open(path, 'rb') as f:
        data_bytes = f.read()
    return bytes_to_data(data_bytes, path.split(".")[-1])
    
# Re-upload data to GCS based on file extension
def reupload_data_to_gcs(data: Union[mne.io.BaseRaw, Dict[str, np.ndarray],
                                     pd.DataFrame, np.ndarray],
                         gs_path: str) -> None:
    """
    Re-upload data to GCS, saving the file in the appropriate format based on the file extension.
    
    Args:
        data: The data to be saved. Could be EEG data, numpy arrays, pandas DataFrame, or media data.
        gs_path: Google Cloud Storage path (gs://bucket_name/blob_name) where the file should be uploaded.
    
    Raises:
        ValueError: If the file extension is not supported.
    """
    # Initialize Google Cloud Storage client
    storage_client = storage.Client()
    
    # Extract bucket and blob names from the `gs://` path
    if gs_path.startswith("gs://"):
        gs_path = gs_path[5:]
    bucket_name, blob_path = gs_path.split("/", 1)
    
    # Get bucket and blob objects
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Determine the file extension and save data accordingly
    if blob_path.endswith(".bdf"):
        # Save EEG data to .bdf file
        bytes_io = save_bdf(data)
    elif blob_path.endswith(".npz"):
        # Save numpy arrays to .npz file
        bytes_io = save_npz(data)
    elif blob_path.endswith(".parquet"):
        # Save pandas DataFrame to parquet file
        bytes_io = save_parquet(data)
    elif blob_path.endswith(('.mp4', '.avi', '.mov')):
        # Save video data as a video file
        bytes_io = save_video(data, blob_path)
    elif blob_path.endswith(('.mp3', '.wav')):
        # Save audio data as an audio file
        bytes_io = save_audio(data, blob_path)
    else:
        raise ValueError("Unsupported file format")

    # Re-upload the file to GCS
    blob.upload_from_file(bytes_io, rewind=True)
    print(f"File uploaded to: {gs_path}")