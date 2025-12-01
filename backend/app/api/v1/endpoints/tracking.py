"""
Tracking endpoint for historical analysis and trends
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from loguru import logger

from app.models.database import get_db, User, Session as DBSession, AIResult, Questionnaire, Alert
from app.models.schemas import TrackingResponse, SessionSummary, TrendAnalysis, AlertResponse, TrackingStatistics

router = APIRouter()


@router.get("/{user_id}", response_model=TrackingResponse)
async def get_tracking(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get tracking dashboard data for a user

    Returns historical sessions, trends, alerts, and statistics
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get user sessions with AI results
        sessions = db.query(DBSession).filter(DBSession.user_id == user_id).order_by(DBSession.created_at.desc()).limit(30).all()

        # Build session summaries
        session_summaries = []
        for session in sessions:
            ai_result = db.query(AIResult).filter(AIResult.session_id == session.id).first()
            questionnaire = db.query(Questionnaire).filter(Questionnaire.session_id == session.id).first()

            if ai_result and questionnaire:
                session_summaries.append(SessionSummary(
                    date=session.created_at,
                    severity_score=ai_result.severity_score,
                    inflammation_score=ai_result.inflammation_score,
                    dryness_score=ai_result.dryness_score,
                    affected_area_pct=ai_result.affected_area_pct,
                    itch_intensity=questionnaire.itch_intensity,
                    flare_status=ai_result.flare_status
                ))

        # Get alerts
        alerts = db.query(Alert).filter(Alert.user_id == user_id).order_by(Alert.created_at.desc()).limit(10).all()
        alert_responses = [
            AlertResponse(
                type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                recommendations=alert.recommendations,
                created_at=alert.created_at
            )
            for alert in alerts
        ]

        # Calculate trends (placeholder - will be implemented with flare detector)
        trend = TrendAnalysis(
            direction="stable",
            change_percentage=0.0,
            trend_period_days=7
        )

        # Calculate statistics (placeholder)
        stats = TrackingStatistics(
            total_sessions=len(session_summaries),
            average_severity=sum(s.severity_score for s in session_summaries) / len(session_summaries) if session_summaries else 0.0,
            flare_frequency="Insufficient data",
            most_common_triggers=[],
            treatment_adherence_pattern="N/A"
        )

        return TrackingResponse(
            user_id=user_id,
            sessions=session_summaries,
            trends=trend,
            alerts=alert_responses,
            statistics=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tracking retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tracking data: {str(e)}"
        )
