"""
Main API Router
"""
from fastapi import APIRouter

from app.api.routes import extract2markdown, filter2csv, transform2tidy


# Create main router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    extract2markdown.router,
    prefix="/extract",
    tags=["Extract"]
)

api_router.include_router(
    filter2csv.router,
    prefix="/filter",
    tags=["Filter"]
)

api_router.include_router(
    transform2tidy.router,
    prefix="/transform",
    tags=["Transform"]
)