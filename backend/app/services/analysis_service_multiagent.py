"""
Multi-Agent Analysis Service
Orchestrates CNN, Vision Agent, EASI Agent, and Report Generation
"""
from typing import Dict
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger
import os
import asyncio

from app.services.cnn_service import cnn_service
from app.services.gradcam_service import gradcam_service
from app.agents.vision_agent import ad_vision_agent
from app.agents.easi_agent import easi_agent
from app.models.database import Session as DBSession, AIResult, Report, Questionnaire
from app.core.config import settings


class MultiAgentAnalysisService:
    """Orchestrates the complete multi-agent analysis pipeline"""

    async def process_session(self, session_id: UUID, db: Session):
        """
        Process a complete analysis session using multi-agent architecture

        Pipeline:
        1. CNN Analysis (EfficientNet-B7)
        2. Vision Agent Analysis (Gemini 1.5 Pro + RAG)
        3. EASI Scoring Agent (Gemini 1.5 Pro + RAG)
        4. Generate Dual Reports
        5. GradCAM Saliency Maps

        Args:
            session_id: Session UUID to process
            db: Database session
        """
        try:
            logger.info(f"Starting multi-agent analysis for session: {session_id}")

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
            logger.info("[1/5] Running CNN analysis...")
            cnn_results = cnn_service.analyze_image(
                session.image_path,
                questionnaire_dict
            )
            logger.success(f"CNN analysis complete: Severity={cnn_results['severity_score']:.1f}")

            # Step 2: Vision Agent Analysis (with RAG)
            logger.info("[2/5] Running Vision Agent analysis...")
            vision_response = await ad_vision_agent.process(
                input_data={
                    "image_path": session.image_path,
                    "body_area": questionnaire.primary_location,
                    "symptoms": f"Itch: {questionnaire.itch_intensity}/10",
                    "has_history": questionnaire.atopic_triad_history,
                    "use_rag": True
                }
            )

            if not vision_response.success:
                logger.error(f"Vision agent failed: {vision_response.error}")
                vision_findings = {}
            else:
                vision_findings = vision_response.data
                logger.success(f"Vision analysis complete (confidence: {vision_response.confidence:.2f})")

            # Step 3: EASI Scoring Agent (with RAG)
            logger.info("[3/5] Calculating EASI score...")
            easi_response = await easi_agent.process(
                input_data={
                    "action": "calculate_easi",
                    "vision_findings": vision_findings,
                    "questionnaire_data": questionnaire_dict,
                    "use_rag": True
                }
            )

            if not easi_response.success:
                logger.error(f"EASI agent failed: {easi_response.error}")
                easi_results = {"easi_calculation": {"total_easi": 0}}
            else:
                easi_results = easi_response.data
                total_easi = easi_results.get("easi_calculation", {}).get("total_easi", 0)
                logger.success(f"EASI calculation complete: Total EASI = {total_easi}")

            # Step 4: Generate Saliency Map
            logger.info("[4/5] Generating saliency map...")
            saliency_map_path = os.path.join(
                settings.STORAGE_PATH,
                "saliency_maps",
                f"{session_id}.png"
            )
            gradcam_service.generate_saliency_map(
                session.image_path,
                saliency_map_path
            )

            # Step 5: Save AI Results (CNN + Vision + EASI combined)
            logger.info("[5/5] Saving integrated AI results...")
            ai_result = AIResult(
                session_id=session_id,
                # Primary scores from CNN
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

            # Step 6: Generate Dual Reports
            logger.info("Generating dual reports from multi-agent results...")

            # User Report
            user_report = self._generate_user_report(
                cnn_results, vision_findings, easi_results, questionnaire_dict
            )

            # HCP Report
            hcp_report = self._generate_hcp_report(
                cnn_results, vision_findings, easi_results, questionnaire_dict, saliency_map_path
            )

            # Save reports
            user_report_db = Report(
                session_id=session_id,
                report_type='user',
                content=user_report
            )
            db.add(user_report_db)

            hcp_report_db = Report(
                session_id=session_id,
                report_type='hcp',
                content=hcp_report
            )
            db.add(hcp_report_db)

            db.commit()

            logger.success(f"Multi-agent analysis complete for session: {session_id}")
            logger.info(f"Total cost estimate: ${(vision_response.cost or 0) + (easi_response.cost or 0):.4f}")

        except Exception as e:
            logger.error(f"Error in multi-agent analysis pipeline: {e}")
            db.rollback()
            raise

    def _generate_user_report(
        self, cnn_results: Dict, vision_findings: Dict, easi_results: Dict, questionnaire: Dict
    ) -> Dict:
        """Generate user-friendly report from multi-agent results"""
        easi_calc = easi_results.get("easi_calculation", {})
        total_easi = easi_calc.get("total_easi", cnn_results['severity_score'])
        severity_cat = easi_calc.get("severity_category", "Moderate")

        return {
            "type": "user",
            "severity": severity_cat,
            "summary": f"Analysis complete. Your AD severity is {severity_cat.lower()}.",
            "key_findings": [
                f"EASI Score: {total_easi:.1f}/72",
                f"CNN Severity: {cnn_results['severity_score']:.1f}/100",
                f"Affected Area: {cnn_results['affected_area_pct']:.1f}%"
            ],
            "recommendations": [
                "Continue daily moisturizer routine",
                "Consult with your dermatologist about treatment",
                "Track symptoms and flare triggers"
            ],
            "when_to_seek_help": "Contact your doctor if symptoms worsen or don't improve in 7-10 days."
        }

    def _generate_hcp_report(
        self, cnn_results: Dict, vision_findings: Dict, easi_results: Dict,
        questionnaire: Dict, saliency_map_path: str
    ) -> Dict:
        """Generate HCP clinical report from multi-agent results"""
        easi_calc = easi_results.get("easi_calculation", {})
        total_easi = easi_calc.get("total_easi", 0)

        return {
            "type": "hcp",
            "integrated_assessment": {
                "cnn_severity": cnn_results['severity_score'],
                "easi_score": total_easi,
                "severity_category": easi_calc.get("severity_category", "Unknown"),
                "agent_consensus": "CNN and EASI scoring aligned" if abs(
                    cnn_results['severity_score'] - total_easi) < 15 else "Discrepancy noted"
            },
            "easi_breakdown": easi_calc,
            "cnn_analysis": cnn_results,
            "vision_agent_findings": vision_findings,
            "clinical_interpretation": easi_results.get("clinical_interpretation", {}),
            "treatment_recommendations": [],
            "saliency_map_url": f"/storage/saliency_maps/{os.path.basename(saliency_map_path)}",
            "rag_enhanced": True
        }


# Global instance
multiagent_analysis_service = MultiAgentAnalysisService()
