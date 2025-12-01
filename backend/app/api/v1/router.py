"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import upload, analysis, reports, tracking

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
