"""
Transform to Tidy Route
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.logger import logger
from app.core.exeception import AppException
from app.models.schemas import TransformRequest, TransformResponse
from app.services.file_locator import get_cleaned_table_csv
from app.services.transform2tidy.pipeline.orchestrator import run_transform_pipeline
from app.utils.timer import Timer


router = APIRouter()


@router.post("/tidy", response_model=TransformResponse)
async def transform_to_tidy(request: TransformRequest):
    """
    Transform CSV table to tidy dataset using LLM-driven cleaning
    """
    timer = Timer()
    timer.start()
    
    file_id = request.file_id
    table_id = request.table_id
    
    try:
        logger.info(f"Starting transform pipeline for {file_id}/{table_id}")
        
        result = run_transform_pipeline(file_id, table_id)
        logger.info("Transform pipeline finished for %s/%s", file_id, table_id)
        
        processing_time = timer.stop()
        
        return TransformResponse(
            file_id=file_id,
            table_id=table_id,
            cleaned_csv_path=str(result["cleaned_csv_path"]),
            profile_path=str(result["profile_path"]),
            num_rows_original=result["num_rows_original"],
            num_rows_cleaned=result["num_rows_cleaned"],
            processing_time=processing_time,
            cleaning_summary=result.get("summary", {}),
            message="Transform completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Transform error for {file_id}/{table_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Transform failed: {str(e)}"
        )


@router.get("/download/cleaned/{file_id}/{table_id}")
async def download_cleaned_table(file_id: str, table_id: str):
    """Allow clients to download a cleaned CSV produced by the transform pipeline."""
    try:
        csv_path = get_cleaned_table_csv(file_id, table_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return FileResponse(
        path=csv_path,
        filename=csv_path.name,
        media_type="text/csv"
    )