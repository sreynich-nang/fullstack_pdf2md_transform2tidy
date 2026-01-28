"""
File Management Utilities
"""
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logger import logger
from app.core.exeception import FileNotFoundException


class FileManager:
    """File management utility class"""
    
    def __init__(self):
        self.base_dir = settings.base_dir
    
    def ensure_directories(self):
        """Create all required directories"""
        directories = [
            settings.TEMP_DIR,
            settings.UPLOADS_DIR,
            settings.OUTPUTS_DIR,
            settings.PDF2IMAGE_DIR,
            settings.EACH_TABLE_DIR,
            settings.TRANSFORM_DIR,
            settings.CLEANED_DATA_DIR,
            settings.PROFILE_RAW_DF_DIR,
            settings.PROMPT1_PROFILE_DIR,
            settings.PROMPT2_PROMPT1_DIR,
            settings.PROMPT3_PROMPT2_DIR,
            settings.LOGS_DIR,
        ]
        
        for directory in directories:
            dir_path = settings.get_path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    
    def save_upload(self, file_content: bytes, filename: str) -> Path:
        """Save uploaded file"""
        upload_dir = settings.get_path(settings.UPLOADS_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        unique_filename = f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"
        
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"Saved upload: {file_path}")
        return file_path
    
    def get_file(self, file_id: str, directory: str) -> Path:
        """Get file path by ID"""
        dir_path = settings.get_path(directory)
        
        # Search for file with matching ID
        for file_path in dir_path.glob(f"*{file_id}*"):
            if file_path.is_file():
                return file_path
        
        raise FileNotFoundException(f"{file_id} in {directory}")
    
    def list_files(self, directory: str, pattern: str = "*") -> List[Path]:
        """List files in directory"""
        dir_path = settings.get_path(directory)
        
        if not dir_path.exists():
            return []
        
        return sorted([f for f in dir_path.glob(pattern) if f.is_file()])
    
    def delete_file(self, file_path: Path) -> bool:
        """Delete a file"""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def cleanup_old_files(self, directory: str, days: int = 7):
        """Clean up files older than specified days"""
        dir_path = settings.get_path(directory)
        
        if not dir_path.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    self.delete_file(file_path)
                    deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old files from {directory}")
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        return file_path.stat().st_size if file_path.exists() else 0
    
    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension"""
        if "." not in filename:
            return False
        
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in settings.allowed_extensions_list