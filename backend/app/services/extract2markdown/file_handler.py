from fastapi import UploadFile
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.exeception import FileNotFoundException, InvalidFileTypeException


class FileHandler:
    """Manage uploaded files for the extract-to-markdown workflow."""

    def __init__(self, uploads_dir: Optional[Path] = None):
        self.uploads_dir = uploads_dir or settings.get_path(settings.UPLOADS_DIR)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_suffixes = {
            f".{ext.lower().lstrip('.')}" for ext in settings.allowed_extensions_list
        }

    async def save_upload(self, upload_file: UploadFile) -> Path:
        """Validate and persist an UploadFile to the uploads directory."""
        safe_name = Path(upload_file.filename or "upload").name
        suffix = Path(safe_name).suffix.lower()

        if suffix not in self.allowed_suffixes:
            content_type = (getattr(upload_file, "content_type", None) or "").lower()
            if not (content_type.startswith("image/") or content_type == "application/pdf"):
                raise InvalidFileTypeException(
                    suffix or content_type,
                    settings.allowed_extensions_list,
                )

        target = self.uploads_dir / safe_name
        with target.open("wb") as buffer:
            buffer.write(await upload_file.read())
        return target

    def _find_candidates(self, file_id: str) -> List[Path]:
        pattern = f"*{file_id}*"
        return sorted(
            [p for p in self.uploads_dir.glob(pattern) if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def get_uploaded_file(self, file_id: str) -> Path:
        """Locate an uploaded file by ID (matches any filename containing the ID)."""
        candidates = self._find_candidates(file_id)
        if not candidates:
            raise FileNotFoundException(file_id)
        return candidates[0]

    def list_uploads(self) -> List[Path]:
        """Return uploads ordered by most recent first."""
        return self._find_candidates("")
