"""
Reports endpoint for retrieving user/HCP reports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Union
from loguru import logger

from app.models.database import get_db, Report
from app.models.schemas import UserReportResponse, HCPReportResponse

router = APIRouter()


@router.get("/{session_id}", response_model=Union[UserReportResponse, HCPReportResponse])
async def get_report(
    session_id: UUID,
    type: str = Query("user", regex="^(user|hcp)$", description="Report type: user or hcp"),
    db: Session = Depends(get_db)
):
    """
    Get report for a session

    Query parameter 'type' determines user or HCP report
    """
    try:
        # Get report
        report = db.query(Report).filter(
            Report.session_id == session_id,
            Report.report_type == type
        ).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found for session {session_id}"
            )

        # Return report based on type
        if type == "user":
            return UserReportResponse(**report.content)
        else:
            return HCPReportResponse(**report.content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}"
        )
