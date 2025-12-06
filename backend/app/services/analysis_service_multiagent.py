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
from app.services.activation_map_service import activation_map_service
from app.services.clinical_note_service import clinical_note_service
from app.agents.vision_agent import ad_vision_agent
from app.agents.easi_agent import easi_agent
from app.models.database import Session as DBSession, AIResult, Report, Questionnaire
from app.core.config import settings


class MultiAgentAnalysisService:
    """Orchestrates the complete multi-agent analysis pipeline"""

    async def process_session(self, session_id: UUID):
        """
        Process a complete analysis session using multi-agent architecture

        Pipeline:
        1. CNN Analysis (EfficientNet-B7)
        2. Vision Agent Analysis (Gemini 1.5 Pro + RAG)
        3. EASI Scoring Agent (Gemini 1.5 Pro + RAG)
        4. Generate Dual Reports
        5. Activation Map Saliency Maps

        Args:
            session_id: Session UUID to process
        """
        # Create new DB session for background task (NOT request-scoped!)
        from app.models.database import SessionLocal
        db = SessionLocal()

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

            # Step 1 & 2: Run CNN and Vision Agent in PARALLEL (major speedup!)
            logger.info("[1/4] Running CNN and Vision Agent in parallel...")

            # Run CNN and Vision Agent concurrently using asyncio.gather
            cnn_task = asyncio.to_thread(
                cnn_service.analyze_image,
                session.image_path,
                questionnaire_dict
            )

            vision_task = ad_vision_agent.process(
                input_data={
                    "image_path": session.image_path,
                    "body_area": questionnaire.primary_location,
                    "symptoms": f"Itch: {questionnaire.itch_intensity}/10",
                    "has_history": questionnaire.atopic_triad_history,
                    "use_rag": True
                }
            )

            # Wait for both to complete
            cnn_results, vision_response = await asyncio.gather(cnn_task, vision_task)

            logger.success(f"CNN analysis complete: Severity={cnn_results['severity_score']:.1f}")

            if not vision_response.success:
                logger.error(f"Vision agent failed: {vision_response.error}")
                vision_findings = {}
            else:
                vision_findings = vision_response.data
                logger.success(f"Vision analysis complete (confidence: {vision_response.confidence:.2f})")

            # Step 2: EASI Scoring Agent (with RAG) - depends on Vision findings
            logger.info("[2/4] Calculating EASI score...")
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
                # Use CNN severity as fallback (0-100 scale → 0-72 EASI scale)
                fallback_easi = (cnn_results['severity_score'] / 100) * 72
                severity_cat = "Moderate" if fallback_easi < 21 else "Severe"
                if fallback_easi < 7:
                    severity_cat = "Mild"
                easi_results = {
                    "easi_calculation": {
                        "total_easi": round(fallback_easi, 1),
                        "severity_category": severity_cat
                    }
                }
                logger.warning(f"Using CNN-based EASI fallback: {fallback_easi:.1f}")
            else:
                easi_results = easi_response.data or {}
                total_easi = easi_results.get("easi_calculation", {}).get("total_easi", 0)
                logger.success(f"EASI calculation complete: Total EASI = {total_easi}")

            # Step 3: Save AI Results (CNN + Vision + EASI combined)
            logger.info("[3/5] Saving integrated AI results...")
            saliency_map_path = os.path.join(
                settings.STORAGE_PATH,
                "saliency_maps",
                f"{session_id}.png"
            )

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

            # Step 4: Generate Dual Reports IMMEDIATELY (don't wait for saliency map)
            logger.info("[4/5] Generating dual reports from multi-agent results...")

            # User Report
            user_report = self._generate_user_report(
                cnn_results, vision_findings, easi_results, questionnaire_dict
            )

            # HCP Report (without saliency map initially - will be added later)
            hcp_report = self._generate_hcp_report(
                cnn_results, vision_findings, easi_results, questionnaire_dict, None
            )

            # Save reports IMMEDIATELY - don't wait for saliency map
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
            logger.success("Reports saved and available for retrieval")

            # Step 5: Generate Saliency Map in background (non-blocking)
            logger.info("[5/5] Starting saliency map generation in background...")
            # Run Activation Map in background thread - this won't block report availability
            activation_task = asyncio.to_thread(
                activation_map_service.generate_saliency_map,
                session.image_path,
                saliency_map_path,
                cnn_service.model,  # Pass the loaded CNN model for real Activation Map
                "top_conv",  # layer_name parameter
                str(session_id)  # Pass session_id for Cloud Storage upload
            )

            # Wait for saliency map to complete
            activation_results = await activation_task
            logger.success("Saliency map generation complete")

            # Update HCP report with saliency map URL and metrics
            logger.info("Updating HCP report with saliency map...")
            updated_hcp_content = self._generate_hcp_report(
                cnn_results, vision_findings, easi_results, questionnaire_dict, activation_results
            )
            hcp_report_db.content = updated_hcp_content
            db.commit()
            logger.success("HCP report updated with saliency map and OpenCV metrics")

            logger.success(f"Multi-agent analysis complete for session: {session_id}")
            logger.info(f"Total cost estimate: ${(vision_response.cost or 0) + (easi_response.cost or 0):.4f}")

        except Exception as e:
            logger.error(f"Error in multi-agent analysis pipeline: {e}")
            db.rollback()
            raise
        finally:
            # IMPORTANT: Close DB session created for background task
            db.close()

    def _generate_user_report(
        self, cnn_results: Dict, vision_findings: Dict, easi_results: Dict, questionnaire: Dict
    ) -> Dict:
        """Generate user-friendly report from multi-agent results"""
        easi_calc = easi_results.get("easi_calculation", {})
        total_easi = easi_calc.get("total_easi") or cnn_results['severity_score']
        severity_cat = easi_calc.get("severity_category") or "Moderate"

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
        questionnaire: Dict, activation_results: Dict
    ) -> Dict:
        """Generate HCP clinical report from multi-agent results with clinical note"""
        easi_calc = easi_results.get("easi_calculation", {})
        total_easi = easi_calc.get("total_easi", 0)

        # Generate SOAP-formatted clinical note
        clinical_note = clinical_note_service.generate_soap_note(
            cnn_results=cnn_results,
            vision_findings=vision_findings,
            easi_results=easi_results,
            questionnaire=questionnaire
        )

        # Use public_url from GCS if available, otherwise fallback to local path
        saliency_map_url = activation_results.get("public_url") if activation_results else None
        if not saliency_map_url and activation_results:
            # Fallback to local path for development
            saliency_map_url = f"/storage/saliency_maps/{os.path.basename(activation_results.get('path', ''))}"

        return {
            "type": "hcp",
            "integrated_assessment": {
                "cnn_severity": cnn_results['severity_score'],
                "easi_score": total_easi,
                "severity_category": easi_calc.get("severity_category", "Unknown")
            },
            "clinical_note": clinical_note,  # SOAP-formatted clinical note
            "easi_breakdown": easi_calc,
            "cnn_analysis": cnn_results,
            "vision_agent_findings": vision_findings,
            "clinical_interpretation": easi_results.get("clinical_interpretation", {}),
            "treatment_recommendations": easi_results.get("clinical_interpretation", {}).get("treatment_implications", []) if easi_results.get("clinical_interpretation") else [],
            "saliency_map_url": saliency_map_url,  # GCS public URL in production
            "saliency_map_metrics": {
                "lesion_count": activation_results.get("lesion_count", 0) if activation_results else 0,
                "erythema_percentage": activation_results.get("erythema_percentage", 0) if activation_results else 0,
                "activation_used": activation_results.get("activation_used", False) if activation_results else False
            },
            "rag_enhanced": True
        }


# Global instance
multiagent_analysis_service = MultiAgentAnalysisService()
