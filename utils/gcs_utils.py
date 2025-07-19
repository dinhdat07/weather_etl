# utils/gcs_utils.py

import os
from google.cloud import storage
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_gcs_client():
    try:
        return storage.Client()
    except Exception as e:
        logger.exception("Failed to create GCS client")
        raise

def check_blob_exists(bucket_name: str, blob_name: str) -> bool:
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    return bucket.blob(blob_name).exists()

def download_blob_as_string(bucket_name: str, blob_name: str) -> str:
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()

def upload_blob_from_string(bucket_name: str, blob_name: str, data: str, content_type: str = "text/csv"):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data, content_type=content_type)

def download_blob_to_file(bucket_name: str, blob_name: str, local_path: str):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
    print(f"[GCS] Downloaded {blob_name} to {local_path}")

def upload_blob_from_file(bucket_name: str, blob_name: str, local_path: str, content_type: str = "text/csv"):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path, content_type=content_type)
    print(f"[GCS] Uploaded {local_path} to gs://{bucket_name}/{blob_name}")


