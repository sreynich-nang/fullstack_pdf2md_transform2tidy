"""
Filter to CSV Route
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import FilterResponse, TableInfo
from app.core.logger import logger
from app.core.exeception import AppException
from app.services.filter2csv.table_extractor import TableExtractor
from app.services.file_locator import get_raw_table_csv
from app.utils.timer import Timer


router = APIRouter()


@router.post("/tables/{file_id}", response_model=FilterResponse)
async def filter_tables(file_id: str):
    """
    Extract tables from markdown and save as CSV files
    """
    timer = Timer()
    timer.start()
    
    try:
        extractor = TableExtractor()
        extraction_result = extractor.extract(file_id)

        csv_files = extraction_result["csv_files"]
        dataframes = extraction_result["tables"]

        table_infos = []
        for _, (df, csv_path) in enumerate(zip(dataframes, csv_files), start=1):
            table_infos.append(
                TableInfo(
                    table_id=csv_path.stem,
                    csv_path=str(csv_path),
                    num_rows=df.shape[0],
                    num_columns=df.shape[1],
                )
            )
        
        processing_time = timer.stop()
        
        logger.info(f"Extracted {len(table_infos)} tables from {file_id}")
        
        return FilterResponse(
            file_id=file_id,
            tables=table_infos,
            total_tables=len(table_infos),
            processing_time=processing_time,
            message=f"Extracted {len(table_infos)} tables successfully"
        )
    
    except Exception as e:
        logger.error(f"Table extraction error for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Table extraction failed: {str(e)}"
        )


@router.get("/download/table/{file_id}/{table_id}")
async def download_table_csv(file_id: str, table_id: str):
    """Send one of the raw CSV tables back to the client for download."""
    try:
        csv_path = get_raw_table_csv(file_id, table_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return FileResponse(
        path=csv_path,
        filename=csv_path.name,
        media_type="text/csv"
    )