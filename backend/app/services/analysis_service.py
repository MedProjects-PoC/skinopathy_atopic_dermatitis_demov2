"""
Analysis Service - Orchestrates CNN, GradCAM, and VLM
"""
from typing import Dict
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger
import os

from app.services.cnn_service import cnn_service
from app.services.gradcam_service import gradcam_service
from app.services.vlm_service import vlm_service
from app.models.database import Session as DBSession, AIResult, Report, Questionnaire
from app.core.config import settings


class AnalysisService:
    """Orchestrates the complete analysis pipeline"""

    async def process_session(self, session_id: UUID, db: Session):
        """
        Process a complete analysis session

        Args:
            session_id: Session UUID to process
            db: Database session
        """
        try:
            logger.info(f"Starting analysis for session: {session_id}")

            # Get session and questionnaire
            session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not session:
                logger.error(f"Session not found: {session_id}")
                return

            questionnaire = db.query(Questionnaire).filter(
                Questionnaire.session_id == session_id
            ).first()
            if not questionnaire:
                logger.error(f"Questionnaire not found for session: {session_id}")
                return

            # Convert questionnaire to dict
            questionnaire_dict = {
                'itch_intensity': questionnaire.itch_intensity,
                'chronic_relapsing': questionnaire.chronic_relapsing,
                'atopic_triad_history': questionnaire.atopic_triad_history,
                'primary_location': questionnaire.primary_location,
                'household_itchy_or_nighttime_worse': questionnaire.household_itchy_or_nighttime_worse,
                'new_exposure_trigger': questionnaire.new_exposure_trigger,
                'thick_silvery_scales': questionnaire.thick_silvery_scales,
                'nights_sleep_disturbed': questionnaire.nights_sleep_disturbed,
                'oozing_honey_crusts': questionnaire.oozing_honey_crusts,
                'steroid_use_last_2weeks': questionnaire.steroid_use_last_2weeks,
                'moisturizer_frequency': questionnaire.moisturizer_frequency,
                'recent_stress_level': questionnaire.recent_stress_level
            }

            # Step 1: CNN Analysis
            logger.info("Running CNN analysis...")
            cnn_results = cnn_service.analyze_image(
                session.image_path,
                questionnaire_dict
            )

            # Step 2: Generate Saliency Map
            logger.info("Generating saliency map...")
            saliency_map_path = os.path.join(
                settings.STORAGE_PATH,
                "saliency_maps",
                f"{session_id}.png"
            )
            gradcam_service.generate_saliency_map(
                session.image_path,
                saliency_map_path
            )

            # Step 3: Save AI Results
            logger.info("Saving AI results...")
            ai_result = AIResult(
                session_id=session_id,
                severity_score=cnn_results['severity_score'],
                affected_area_pct=cnn_results['affected_area_pct'],
                inflammation_score=cnn_results['inflammation_score'],
                dryness_score=cnn_results['dryness_score'],
                lichenification_score=cnn_results['lichenification_score'],
                excoriation_detected=cnn_results['excoriation_detected'],
                flare_status=cnn_results['flare_status'],
                body_regions=cnn_results['body_regions'],
                saliency_map_path=saliency_map_path,
                cnn_confidence=cnn_results['cnn_confidence']
            )
            db.add(ai_result)
            db.commit()

            # Step 4: Generate Dual Reports
            logger.info("Generating dual reports...")
            user_report, hcp_report = vlm_service.generate_dual_reports(
                session.image_path,
                cnn_results,
                questionnaire_dict,
                saliency_map_path
            )

            # Step 5: Save Reports
            logger.info("Saving reports...")

            # Save user report
            user_report_db = Report(
                session_id=session_id,
                report_type='user',
                content=user_report
            )
            db.add(user_report_db)

            # Save HCP report
            hcp_report_db = Report(
                session_id=session_id,
                report_type='hcp',
                content=hcp_report
            )
            db.add(hcp_report_db)

            db.commit()

            logger.success(f"Analysis complete for session: {session_id}")

        except Exception as e:
            logger.error(f"Error in analysis pipeline: {e}")
            db.rollback()
            raise


# Global instance
analysis_service = AnalysisService()
