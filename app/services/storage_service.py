"""
Local Disk Storage Service
Stores uploaded files on the local filesystem under UPLOAD_FOLDER.
Swap this file for the GCS version when moving to production.
"""
import os
import shutil
from uuid import uuid4
from typing import Optional, BinaryIO
from flask import current_app


class StorageService:
    """Service for handling file uploads to local disk."""

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @classmethod
    def _upload_root(cls) -> str:
        """Absolute path to the uploads root directory."""
        folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.isabs(folder):
            folder = os.path.join(current_app.root_path, '..', folder)
        folder = os.path.normpath(folder)
        os.makedirs(folder, exist_ok=True)
        return folder

    @classmethod
    def _base_url(cls) -> str:
        """Base URL used to build public-facing photo URLs."""
        return current_app.config.get('BASE_URL', 'http://localhost:5000')

    # ------------------------------------------------------------------ #
    # Public interface (same as GCS version)                               #
    # ------------------------------------------------------------------ #

    @classmethod
    def upload_file(
        cls,
        file: BinaryIO,
        filename: str,
        folder: str = '',
        content_type: Optional[str] = None
    ) -> dict:
        """
        Save a file to local disk.

        Returns:
            dict with blob_path, public_url, file_size, content_type, bucket
        """
        root = cls._upload_root()

        # Generate unique filename to avoid collisions
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        unique_filename = f"{uuid4()}.{ext}" if ext else str(uuid4())

        # Build the relative blob path (mirrors GCS folder structure)
        blob_path = f"{folder}/{unique_filename}" if folder else unique_filename

        # Full path on disk
        full_dir = os.path.join(root, *folder.split('/')) if folder else root
        os.makedirs(full_dir, exist_ok=True)
        full_path = os.path.join(full_dir, unique_filename)

        # Write file to disk
        file.seek(0)
        with open(full_path, 'wb') as f:
            shutil.copyfileobj(file, f)

        file_size = os.path.getsize(full_path)
        public_url = f"{cls._base_url()}/api/photos/file/{blob_path}"

        return {
            'blob_path': blob_path,
            'public_url': public_url,
            'file_size': file_size,
            'content_type': content_type or 'application/octet-stream',
            'bucket': 'local',
        }

    @classmethod
    def delete_file(cls, blob_path: str) -> bool:
        """Delete a file from local disk."""
        full_path = os.path.join(cls._upload_root(), *blob_path.split('/'))
        try:
            os.remove(full_path)
            return True
        except FileNotFoundError:
            return False

    @classmethod
    def get_signed_url(
        cls,
        blob_path: str,
        expiration_minutes: int = 60
    ) -> Optional[str]:
        """Return a direct URL (no signing needed for local disk)."""
        if cls.file_exists(blob_path):
            return f"{cls._base_url()}/api/photos/file/{blob_path}"
        return None

    @classmethod
    def file_exists(cls, blob_path: str) -> bool:
        """Check if a file exists on disk."""
        full_path = os.path.join(cls._upload_root(), *blob_path.split('/'))
        return os.path.isfile(full_path)

    @classmethod
    def make_public(cls, blob_path: str) -> str:
        """Local files are always accessible — just returns the URL."""
        return f"{cls._base_url()}/api/photos/file/{blob_path}"
