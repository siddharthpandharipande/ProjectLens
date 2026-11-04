import os
import re
import uuid
import zipfile
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import settings


class StorageService:
    @staticmethod
    def generate_project_id() -> str:
        """Generate a clean, collision-resistant project identifier."""
        return f"proj_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Strip directory paths and unsafe characters from original filename."""
        base = os.path.basename(filename)
        # Keep alphanumeric, dot, dash, underscore
        cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
        return cleaned or "upload.zip"

    @classmethod
    async def validate_and_save_upload(cls, file: UploadFile) -> Tuple[str, str, int]:
        """
        Validate incoming UploadFile:
        1. Check file extension is .zip.
        2. Stream chunks and enforce MAX_UPLOAD_SIZE_MB limit.
        3. Verify zip integrity with zipfile.is_zipfile and testzip.
        4. Validate that archive contains no path traversal entries (.. or absolute paths).
        Returns:
            Tuple of (sanitized_original_filename, absolute_saved_path, file_size_bytes)
        """
        original_name = file.filename or ""
        if not original_name.lower().endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only .zip archives are supported.",
            )

        sanitized_name = cls.sanitize_filename(original_name)
        storage_id = uuid.uuid4().hex
        target_filename = f"{storage_id}_{sanitized_name}"
        target_path = settings.resolved_upload_dir / target_filename

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        try:
            with open(target_path, "wb") as buffer:
                while chunk := await file.read(chunk_size):
                    total_bytes += len(chunk)
                    if total_bytes > settings.max_upload_size_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=f"Upload size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                        )
                    buffer.write(chunk)
        except Exception:
            # Clean up partial file on error
            if target_path.exists():
                target_path.unlink()
            raise

        if total_bytes == 0:
            if target_path.exists():
                target_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded archive is empty.",
            )

        # Validate ZIP integrity and prevent path traversal
        cls.validate_zip_archive(target_path)

        return sanitized_name, str(target_path.resolve()), total_bytes

    @classmethod
    def validate_zip_archive(cls, zip_path: Path) -> None:
        """
        Check that the file is a valid zip archive, test its CRC checksums,
        and verify that no archive entry contains malicious directory traversal.
        """
        if not zipfile.is_zipfile(zip_path):
            if zip_path.exists():
                zip_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupt or invalid ZIP archive.",
            )

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Test CRC on all items
                corrupt_file = zf.testzip()
                if corrupt_file:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Corrupted file inside archive: {corrupt_file}",
                    )

                # Inspect entries for path traversal
                for name in zf.namelist():
                    cls.validate_safe_zip_entry(name)
        except HTTPException:
            if zip_path.exists():
                zip_path.unlink()
            raise
        except Exception as e:
            if zip_path.exists():
                zip_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to read ZIP archive: {str(e)}",
            )

    @staticmethod
    def validate_safe_zip_entry(entry_name: str) -> None:
        """Ensure archive member path does not attempt path traversal."""
        # Normalize separators
        entry_normalized = entry_name.replace("\\", "/")

        # Deny absolute paths or Windows drive letters
        if (
            entry_normalized.startswith("/")
            or re.match(r"^[a-zA-Z]:", entry_normalized)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archive contains unsafe absolute path entries.",
            )

        # Check for directory traversal sequences
        parts = entry_normalized.split("/")
        if ".." in parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archive contains unsafe relative path traversal entries (..).",
            )
