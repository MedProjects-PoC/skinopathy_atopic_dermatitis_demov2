"""
Upload endpoint for image and questionnaire submission
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import base64
import os
import uuid
import asyncio
from datetime import datetime
from loguru import logger

from app.models.database import get_db, User, Session as DBSession, Questionnaire
from app.models.schemas import UploadRequest, SessionResponse
from app.core.config import settings
from app.services.analysis_service_multiagent import multiagent_analysis_service

router = APIRouter()


def save_image(image_base64: str, session_id: str) -> str:
    """Save uploaded image to storage"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)

        # Create filename with session ID
        filename = f"{session_id}.jpg"
        filepath = os.path.join(settings.STORAGE_PATH, "images", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_data)

        logger.info(f"Image saved: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}"
        )


@router.post("/", response_model=SessionResponse)
async def upload_image_and_questionnaire(
    request: UploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload image and questionnaire for AD analysis

    Returns session_id for tracking the analysis
    """
    try:
        # Create or get demo user (for MVP, we'll use a single demo user)
        demo_email = "demo@skinopathy.com"
        user = db.query(User).filter(User.email == demo_email).first()

        if not user:
            user = User(
                id=uuid.uuid4(),
                email=demo_email,
                role="user",
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created demo user: {demo_email}")

        # Create analysis session
        session = DBSession(
            id=uuid.uuid4(),
            user_id=user.id,
            image_path="",  # Will be updated after saving image
            created_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Created session: {session.id}")

        # Save uploaded image
        image_path = save_image(request.image, str(session.id))

        # Update session with image path
        session.image_path = image_path
        db.commit()

        # Save questionnaire data (12 validated questions)
        questionnaire = Questionnaire(
            id=uuid.uuid4(),
            session_id=session.id,
            # DDx Questions
            itch_intensity=request.questionnaire.itch_intensity,
            chronic_relapsing=request.questionnaire.chronic_relapsing,
            atopic_triad_history=request.questionnaire.atopic_triad_history,
            primary_location=request.questionnaire.primary_location,
            household_itchy_or_nighttime_worse=request.questionnaire.household_itchy_or_nighttime_worse,
            new_exposure_trigger=request.questionnaire.new_exposure_trigger,
            thick_silvery_scales=request.questionnaire.thick_silvery_scales,
            # Clinical Data Capture
            nights_sleep_disturbed=request.questionnaire.nights_sleep_disturbed,
            oozing_honey_crusts=request.questionnaire.oozing_honey_crusts,
            steroid_use_last_2weeks=request.questionnaire.steroid_use_last_2weeks,
            # Management tracking
            moisturizer_frequency=request.questionnaire.moisturizer_frequency,
            recent_stress_level=request.questionnaire.recent_stress_level
        )
        db.add(questionnaire)
        db.commit()

        logger.info(f"Saved questionnaire for session: {session.id}")

        # Trigger multi-agent analysis pipeline (CNN + Vision Agent + EASI Agent + RAG)
        try:
            # Run analysis in background (creates its own DB session)
            asyncio.create_task(multiagent_analysis_service.process_session(session.id))
            logger.info(f"Multi-agent analysis pipeline triggered for session: {session.id}")

        except Exception as e:
            logger.error(f"Error triggering analysis: {e}")

        return SessionResponse(
            session_id=session.id,
            status="processing"
        )

    except Exception as e:
        logger.error(f"Upload error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
