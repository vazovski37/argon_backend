"""
Google Cloud Storage Service
"""
import os
from uuid import uuid4
from typing import Optional, BinaryIO
from flask import current_app
from google.cloud import storage
from google.cloud.exceptions import NotFound


class StorageService:
    """Service for handling file uploads to Google Cloud Storage."""
    
    _client: Optional[storage.Client] = None
    _bucket: Optional[storage.Bucket] = None
    
    @classmethod
    def _get_client(cls) -> storage.Client:
        """Get or create GCS client."""
        if cls._client is None:
            project_id = current_app.config.get('GCS_PROJECT_ID')
            credentials_path = current_app.config.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            if credentials_path and os.path.exists(credentials_path):
                cls._client = storage.Client.from_service_account_json(
                    credentials_path,
                    project=project_id if project_id else None
                )
            else:
                # Use default credentials (ADC)
                cls._client = storage.Client(project=project_id if project_id else None)
        
        return cls._client
    
    @classmethod
    def _get_bucket(cls) -> storage.Bucket:
        """Get or create the storage bucket."""
        if cls._bucket is None:
            client = cls._get_client()
            bucket_name = current_app.config.get('GCS_BUCKET', 'argonauts-photos')
            cls._bucket = client.bucket(bucket_name)
        
        return cls._bucket
    
    @classmethod
    def upload_file(
        cls,
        file: BinaryIO,
        filename: str,
        folder: str = '',
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            file: File object to upload
            filename: Original filename
            folder: Optional folder/prefix for the file
            content_type: MIME type of the file
            
        Returns:
            dict with file info including public URL and GCS path
        """
        bucket = cls._get_bucket()
        
        # Generate unique filename
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        unique_filename = f"{uuid4()}.{ext}" if ext else str(uuid4())
        
        # Build the full blob path
        if folder:
            blob_path = f"{folder}/{unique_filename}"
        else:
            blob_path = unique_filename
        
        # Create blob and upload
        blob = bucket.blob(blob_path)
        
        if content_type:
            blob.content_type = content_type
        
        # Upload from file object
        file.seek(0)  # Ensure we're at the beginning
        blob.upload_from_file(file, content_type=content_type)
        
        # Get file size
        blob.reload()
        file_size = blob.size
        
        # Generate public URL
        public_url = f"https://storage.googleapis.com/{bucket.name}/{blob_path}"
        
        return {
            'blob_path': blob_path,
            'public_url': public_url,
            'file_size': file_size,
            'content_type': content_type or blob.content_type,
            'bucket': bucket.name
        }
    
    @classmethod
    def delete_file(cls, blob_path: str) -> bool:
        """
        Delete a file from Google Cloud Storage.
        
        Args:
            blob_path: The path to the blob in the bucket
            
        Returns:
            True if deleted, False if not found
        """
        try:
            bucket = cls._get_bucket()
            blob = bucket.blob(blob_path)
            blob.delete()
            return True
        except NotFound:
            return False
    
    @classmethod
    def get_signed_url(
        cls,
        blob_path: str,
        expiration_minutes: int = 60
    ) -> Optional[str]:
        """
        Generate a signed URL for private file access.
        
        Args:
            blob_path: The path to the blob in the bucket
            expiration_minutes: How long the URL should be valid
            
        Returns:
            Signed URL string or None if blob doesn't exist
        """
        from datetime import timedelta
        
        try:
            bucket = cls._get_bucket()
            blob = bucket.blob(blob_path)
            
            if not blob.exists():
                return None
            
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )
            return url
        except Exception:
            return None
    
    @classmethod
    def file_exists(cls, blob_path: str) -> bool:
        """Check if a file exists in the bucket."""
        bucket = cls._get_bucket()
        blob = bucket.blob(blob_path)
        return blob.exists()
    
    @classmethod
    def make_public(cls, blob_path: str) -> str:
        """
        Make a blob publicly accessible.
        
        Args:
            blob_path: The path to the blob in the bucket
            
        Returns:
            Public URL
        """
        bucket = cls._get_bucket()
        blob = bucket.blob(blob_path)
        blob.make_public()
        return blob.public_url

