import boto3
from botocore.client import Config
import os
from typing import BinaryIO

class StorageService:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("MINIO_ROOT_USER", "verifundu_admin")
        self.secret_key = os.getenv("MINIO_ROOT_PASSWORD", "dev_minio_password")
        self.bucket = "receipts"
        
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1", # MinIO doesn't care, but boto3 needs it
        )
        
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except:
            self.client.create_bucket(Bucket=self.bucket)

    def upload_file(self, file_obj: BinaryIO, filename: str) -> str:
        """Uploads a file and returns the s3 key."""
        self.client.upload_fileobj(file_obj, self.bucket, filename)
        return f"{self.bucket}/{filename}"

storage = StorageService()
