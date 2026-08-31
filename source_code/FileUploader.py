import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, BinaryIO
from concurrent.futures import ThreadPoolExecutor
import threading


# ---------------------------------------------------------------------------
# Custom Exceptions for Granular Error Handling
# ---------------------------------------------------------------------------
class FileStorageError(Exception):
    """Base exception for file storage operations."""
    pass

class FileSizeLimitExceededError(FileStorageError):
    """Raised when an uploaded file exceeds the configured size limit."""
    pass

class FileNotFoundError(FileStorageError):
    """Raised when requesting a file ID that does not exist."""
    pass

class FileIntegrityError(FileStorageError):
    """Raised when file hash verification fails during transfer."""
    pass

class InvalidFileTypeError(FileStorageError):
    """Raised when the uploaded file extension/MIME type is not allowed."""
    pass


# ---------------------------------------------------------------------------
# Metadata Data Model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FileMetadata:
    file_id: str
    original_name: str
    stored_name: str
    content_type: str
    size_bytes: int
    sha256_checksum: str
    uploaded_at_utc: str
    user_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Production-Grade File Manager
# ---------------------------------------------------------------------------
class ProductionFileManager:
    """
    Thread-safe, persistent file manager designed for high-concurrency production workloads.
    Handles streaming disk I/O, hash verification, metadata indexing, and atomic mutations.
    """

    def __init__(
        self,
        storage_dir: str = "./file_storage",
        max_file_size_bytes: int = 25 * 1024 * 1024,  # 25 MB default limit
        allowed_extensions: Optional[set] = None,
        chunk_size: int = 64 * 1024  # 64 KB read buffer
    ):
        self.storage_dir = Path(storage_dir).resolve()
        self.max_file_size = max_file_size_bytes
        self.chunk_size = chunk_size
        
        # Default allowed file extensions (adjust per business requirements)
        self.allowed_extensions = allowed_extensions or {
            ".png", ".jpg", ".jpeg", ".pdf", ".txt", ".csv", ".docx", ".zip"
        }

        # Initialize storage directory structure
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Thread synchronization primitives
        # RLock allows reentrant operations by the same thread if nested calls occur
        self._lock = threading.RLock()
        
        # In-memory metadata catalog (in multi-instance systems, swap this with Redis/PostgreSQL)
        self._metadata_index: Dict[str, FileMetadata] = {}

    def _sanitize_filename(self, filename: str) -> str:
        """Strips path traversal attempts and extracts secure base names."""
        clean_name = Path(filename).name
        # Remove null bytes and edge-case control characters
        return clean_name.replace("\x00", "").strip()

    def _validate_extension(self, filename: str) -> str:
        """Validates extension against the allowlist and resolves MIME type."""
        ext = Path(filename).suffix.lower()
        if not ext or ext not in self.allowed_extensions:
            raise InvalidFileTypeError(
                f"File extension '{ext}' is not permitted. Allowed: {sorted(self.allowed_extensions)}"
            )
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def upload_stream(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        user_id: Optional[str] = None
    ) -> FileMetadata:
        """
        Processes a binary stream, computes SHA-256 in real-time, enforces size limits,
        and saves to disk without loading the entire payload into RAM at once.
        """
        clean_name = self._sanitize_filename(original_filename)
        mime_type = self._validate_extension(clean_name)

        # Generate collision-free storage identifier
        file_id = str(uuid.uuid4())
        ext = Path(clean_name).suffix.lower()
        stored_filename = f"{file_id}{ext}"
        target_path = self.storage_dir / stored_filename

        hasher = hashlib.sha256()
        total_bytes = 0

        # Stream directly to disk in chunks to keep memory footprint O(1)
        try:
            with open(target_path, "wb") as dest_file:
                while chunk := file_stream.read(self.chunk_size):
                    total_bytes += len(chunk)

                    # Enforce strict size threshold during stream to prevent disk exhaustion
                    if total_bytes > self.max_file_size:
                        raise FileSizeLimitExceededError(
                            f"File exceeded max limit of {self.max_file_size} bytes (processed {total_bytes} bytes)."
                        )

                    hasher.update(chunk)
                    dest_file.write(chunk)

        except Exception:
            # Clean up dangling/corrupted partial files if upload is interrupted or fails
            if target_path.exists():
                target_path.unlink()
            raise

        # Construct immutable metadata
        metadata = FileMetadata(
            file_id=file_id,
            original_name=clean_name,
            stored_name=stored_filename,
            content_type=mime_type,
            size_bytes=total_bytes,
            sha256_checksum=hasher.hexdigest(),
            uploaded_at_utc=datetime.now(timezone.utc).isoformat(),
            user_id=user_id
        )

        # Atomic index mutation
        with self._lock:
            self._metadata_index[file_id] = metadata

        return metadata

    def get_metadata(self, file_id: str) -> FileMetadata:
        """Fetches metadata for a given file ID in a thread-safe manner."""
        with self._lock:
            metadata = self._metadata_index.get(file_id)
            if not metadata:
                raise FileNotFoundError(f"File ID '{file_id}' not found.")
            return metadata

    def list_files(self, user_id: Optional[str] = None) -> List[FileMetadata]:
        """Lists metadata records, optionally filtered by user ID."""
        with self._lock:
            if user_id:
                return [m for m in self._metadata_index.values() if m.user_id == user_id]
            return list(self._metadata_index.values())

    def get_file_path(self, file_id: str) -> Path:
        """Resolves the verified on-disk path for secure file downloads."""
        metadata = self.get_metadata(file_id)
        path = self.storage_dir / metadata.stored_name
        if not path.exists():
            raise FileNotFoundError(f"Physical file missing for ID '{file_id}'.")
        return path

    def delete_file(self, file_id: str) -> None:
        """Deletes both on-disk payload and in-memory registry record atomically."""
        with self._lock:
            metadata = self._metadata_index.get(file_id)
            if not metadata:
                raise FileNotFoundError(f"File ID '{file_id}' not found.")

            target_path = self.storage_dir / metadata.stored_name

            # Remove physical file
            try:
                if target_path.exists():
                    target_path.unlink()
            except OSError as exc:
                raise FileStorageError(f"Failed to delete disk payload: {exc}") from exc

            # Remove registry entry
            del self._metadata_index[file_id]
            
            
# Testing        
            
            
import io

if __name__ == "__main__":
    # Initialize the production manager
    manager = ProductionFileManager(
        storage_dir="./app_uploads",
        max_file_size_bytes=10 * 1024 * 1024  # 10MB
    )

    # 1. Simulate an incoming file stream (e.g., from Flask/FastAPI/Django)
    mock_payload = b"Hello, this is a secure production file upload test."
    stream = io.BytesIO(mock_payload)

    # 2. Upload file
    metadata = manager.upload_stream(
        file_stream=stream,
        original_filename="user_report.txt",
        user_id="user_9482"
    )
    print("Upload Success:")
    print(metadata.to_dict())

    # 3. Retrieve metadata
    meta = manager.get_metadata(metadata.file_id)
    print(f"\nRetrieved: {meta.original_name} ({meta.size_bytes} bytes, SHA: {meta.sha256_checksum})")

    # 4. List all files
    all_files = manager.list_files(user_id="user_9482")
    print(f"\nUser File Count: {len(all_files)}")

    # 5. Clean up / Delete
    manager.delete_file(metadata.file_id)
    print("\nFile successfully deleted.")