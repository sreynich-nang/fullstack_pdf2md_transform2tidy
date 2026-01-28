"""
Path Utilities
"""
from pathlib import Path
from typing import Optional


def get_file_id(file_path: Path) -> str:
    """Extract file ID from filename (removes extension and timestamp)"""
    stem = file_path.stem
    # Try to extract original name before timestamp
    parts = stem.split("_")
    if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) == 14:
        # Timestamp format: YYYYMMDD_HHMMSS
        return "_".join(parts[:-2]) if len(parts) > 2 else parts[0]
    return stem


def ensure_extension(filename: str, extension: str) -> str:
    """Ensure filename has the correct extension"""
    if not extension.startswith("."):
        extension = f".{extension}"
    
    if not filename.endswith(extension):
        return f"{filename}{extension}"
    return filename


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename


def get_relative_path(full_path: Path, base_path: Path) -> str:
    """Get relative path as string"""
    try:
        return str(full_path.relative_to(base_path))
    except ValueError:
        return str(full_path)


def create_output_filename(input_path: Path, suffix: str, extension: str) -> str:
    """Create output filename based on input filename"""
    stem = input_path.stem
    return f"{stem}_{suffix}.{extension.lstrip('.')}"