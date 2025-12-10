"""
Reports endpoint for retrieving user/HCP reports and generating PDFs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Union
from loguru import logger
from io import BytesIO

from app.models.database import get_db, Report
from app.models.schemas import UserReportResponse, HCPReportResponse
from app.services.pdf_service import PDFGenerator

router = APIRouter()


@router.get("/{session_id}")
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

        # Return raw JSON content to avoid schema validation issues
        return report.content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}"
        )


@router.get("/{session_id}/pdf/user")
async def download_user_report_pdf(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Download user-friendly report as PDF

    Returns:
        PDF file for download
    """
    try:
        # Get report
        report = db.query(Report).filter(
            Report.session_id == session_id,
            Report.report_type == "user"
        ).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found for session {session_id}"
            )

        # Generate PDF
        pdf_buffer = PDFGenerator.generate_user_report_pdf(
            session_id=str(session_id),
            report_data=report.content
        )

        return FileResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=AD_Report_User_{session_id}.pdf"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation error for user report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/{session_id}/pdf/hcp")
async def download_hcp_report_pdf(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Download clinical HCP report as PDF

    Returns:
        PDF file for download
    """
    try:
        # Get report
        report = db.query(Report).filter(
            Report.session_id == session_id,
            Report.report_type == "hcp"
        ).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found for session {session_id}"
            )

        # Generate PDF
        pdf_buffer = PDFGenerator.generate_hcp_report_pdf(
            session_id=str(session_id),
            report_data=report.content
        )

        return FileResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=AD_Report_Clinical_{session_id}.pdf"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation error for HCP report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
