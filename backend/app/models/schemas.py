"""
Pydantic Models and Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class UploadResponse(BaseModel):
    """Upload response model"""
    file_id: str
    filename: str
    file_size: int
    upload_time: datetime
    message: str


class ExtractResponse(BaseModel):
    """Extract response model"""
    file_id: str
    markdown_path: str
    num_pages: Optional[int] = None
    processing_time: float
    message: str


class TableInfo(BaseModel):
    """Table information model"""
    table_id: str
    csv_path: str
    num_rows: int
    num_columns: int


class FilterResponse(BaseModel):
    """Filter response model"""
    file_id: str
    tables: List[TableInfo]
    total_tables: int
    processing_time: float
    message: str


class TransformRequest(BaseModel):
    """Transform request model"""
    file_id: str
    table_id: str


class TransformResponse(BaseModel):
    """Transform response model"""
    file_id: str
    table_id: str
    cleaned_csv_path: str
    profile_path: Optional[str] = None
    num_rows_original: int
    num_rows_cleaned: int
    processing_time: float
    cleaning_summary: Dict[str, Any]
    message: str


class PipelineStatus(BaseModel):
    """Pipeline status model"""
    file_id: str
    stage: Literal["uploaded", "extracted", "filtered", "transformed"]
    created_at: datetime
    updated_at: datetime
    artifacts: Dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    stage: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    app: str
    version: str