"""
Custom Exception Classes
"""
from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FileNotFoundException(AppException):
    """File not found exception"""
    def __init__(self, file_path: str):
        super().__init__(
            f"File not found: {file_path}",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidFileTypeException(AppException):
    """Invalid file type exception"""
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            f"Invalid file type: {file_type}. Allowed types: {', '.join(allowed_types)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileTooLargeException(AppException):
    """File too large exception"""
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            f"File too large: {file_size} bytes. Maximum allowed: {max_size} bytes",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )


class ProcessingException(AppException):
    """Processing exception"""
    def __init__(self, stage: str, details: str):
        super().__init__(
            f"Error in {stage}: {details}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MarkerError(ProcessingException):
    """Specialized exception raised for Marker CLI failures."""
    def __init__(self, details: str):
        super().__init__("Marker pipeline", details)


class LLMException(AppException):
    """LLM API exception"""
    def __init__(self, details: str):
        super().__init__(
            f"LLM API error: {details}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TableNotFoundException(AppException):
    """Table not found exception"""
    def __init__(self, table_name: str):
        super().__init__(
            f"Table not found: {table_name}",
            status_code=status.HTTP_404_NOT_FOUND
        )