"""
Extract to Markdown Route
"""
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import UploadResponse, ExtractResponse
from app.core.config import settings
from app.core.logger import logger
from app.core.file_management import FileManager
from app.core.exeception import AppException, InvalidFileTypeException, FileTooLargeException, ProcessingException
from app.services.extract2markdown.file_handler import FileHandler
from app.services.extract2markdown.marker_runner import MarkerRunner
from app.services.file_locator import get_markdown_file
from app.utils.timer import Timer


router = APIRouter()
file_manager = FileManager()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF or image file
    """
    try:
        # Validate file type
        if not file_manager.validate_file_extension(file.filename):
            raise InvalidFileTypeException(
                file.filename.split(".")[-1],
                settings.allowed_extensions_list
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise FileTooLargeException(len(content), settings.MAX_UPLOAD_SIZE)
        
        # Save file
        file_path = file_manager.save_upload(content, file.filename)
        
        logger.info(f"File uploaded successfully: {file.filename}")
        
        return UploadResponse(
            file_id=file_path.stem,
            filename=file.filename,
            file_size=len(content),
            upload_time=datetime.now(),
            message="File uploaded successfully"
        )
    
    except (InvalidFileTypeException, FileTooLargeException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/markdown/{file_id}", response_model=ExtractResponse)
async def extract_to_markdown(file_id: str):
    """
    Extract PDF/Image to Markdown using Marker
    """
    timer = Timer()
    timer.start()
    
    try:
        # Get uploaded file
        file_handler = FileHandler()
        file_path = file_handler.get_uploaded_file(file_id)
        
        # Run marker extraction
        marker_runner = MarkerRunner()
        result = marker_runner.process_file(file_path)
        
        processing_time = timer.stop()
        
        logger.info(f"Markdown extraction completed for {file_id}")
        
        return ExtractResponse(
            file_id=file_id,
            markdown_path=str(result["markdown_path"]),
            num_pages=result.get("num_pages"),
            processing_time=processing_time,
            message="Markdown extraction completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Extraction error for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.get("/download/markdown/{file_id}")
async def download_markdown(file_id: str):
    """Provide the extracted markdown as a downloadable file."""
    try:
        markdown_path = get_markdown_file(file_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return FileResponse(
        path=markdown_path,
        filename=markdown_path.name,
        media_type="text/markdown"
    )