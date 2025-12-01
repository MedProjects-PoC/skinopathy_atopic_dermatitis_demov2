"""
Analysis endpoint for retrieving AI analysis results
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from loguru import logger

from app.models.database import get_db, Session as DBSession, AIResult, Questionnaire
from app.models.schemas import AnalysisResponse, AIResultResponse

router = APIRouter()


@router.get("/{session_id}", response_model=AnalysisResponse)
async def get_analysis(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get AI analysis results for a session

    Returns CNN results and saliency map URL
    """
    try:
        # Get session
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        # Get AI results
        ai_result = db.query(AIResult).filter(AIResult.session_id == session_id).first()
        if not ai_result:
            # Analysis not complete yet
            return AnalysisResponse(
                session_id=session_id,
                status="processing",
                cnn_results=AIResultResponse(
                    severity_score=0.0,
                    affected_area_pct=0.0,
                    inflammation_score=0.0,
                    dryness_score=0.0,
                    lichenification_score=0.0,
                    excoriation_detected=False,
                    flare_status="pending",
                    body_regions={},
                    cnn_confidence=0.0
                ),
                saliency_map_url=""
            )

        # Return completed analysis
        return AnalysisResponse(
            session_id=session_id,
            status="completed",
            cnn_results=AIResultResponse(
                severity_score=ai_result.severity_score,
                affected_area_pct=ai_result.affected_area_pct,
                inflammation_score=ai_result.inflammation_score,
                dryness_score=ai_result.dryness_score,
                lichenification_score=ai_result.lichenification_score,
                excoriation_detected=ai_result.excoriation_detected,
                flare_status=ai_result.flare_status,
                body_regions=ai_result.body_regions or {},
                cnn_confidence=ai_result.cnn_confidence
            ),
            saliency_map_url=f"/storage/saliency_maps/{session_id}.png" if ai_result.saliency_map_path else ""
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )
