"""
Streamlined Analysis Service
Orchestrates CNN + Vision AI with simplified reporting
"""
from typing import Dict
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger
import os
import asyncio

from app.services.cnn_service import cnn_service
from app.agents.vision_agent import ad_vision_agent
from app.models.database import Session as DBSession, AIResult, Report, Questionnaire
from app.core.config import settings


class MultiAgentAnalysisService:
    """Orchestrates the complete multi-agent analysis pipeline"""

    async def process_session(self, session_id: UUID):
        """
        Process a complete analysis session using multi-agent architecture

        Pipeline:
        1. CNN Analysis (EfficientNet-B7)
        2. Vision Agent Analysis (Gemini 2.5 Flash + RAG)
        3. Generate Dual Reports

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
            import time
            parallel_start = time.time()
            logger.info("[1/3] Running CNN and Vision Agent in parallel...")

            # Run CNN and Vision Agent concurrently using asyncio.gather
            cnn_start = time.time()
            cnn_task = asyncio.to_thread(
                cnn_service.analyze_image,
                session.image_path,
                questionnaire_dict
            )

            vision_start = time.time()
            vision_task = ad_vision_agent.process(
                input_data={
                    "image_path": session.image_path,
                    "body_area": questionnaire.primary_location,
                    "symptoms": f"Itch: {questionnaire.itch_intensity}/10",
                    "has_history": questionnaire.atopic_triad_history,
                    "cnn_results": None,  # Will be filled after CNN completes
                    "questionnaire": questionnaire_dict,
                    "use_rag": True
                }
            )
            logger.info(f"⏱️  Tasks created in {(vision_start - cnn_start)*1000:.0f}ms (should be ~0ms if truly parallel)")

            # Wait for both to complete
            cnn_results, vision_response = await asyncio.gather(cnn_task, vision_task)
            parallel_end = time.time()
            parallel_duration = parallel_end - parallel_start

            logger.success(f"CNN analysis complete: Severity={cnn_results['severity_score']:.1f}")
            logger.info(f"⏱️  Parallel execution completed in {parallel_duration:.1f}s (expected ~60-90s with new model)")

            if not vision_response.success:
                logger.error(f"Vision agent failed: {vision_response.error}")
                vision_findings = {}
            else:
                vision_findings = vision_response.data
                logger.success(f"Vision analysis complete (confidence: {vision_response.confidence:.2f})")

            # Step 2: Save AI Results (CNN + Vision combined)
            logger.info("[2/3] Saving integrated AI results...")

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
                cnn_confidence=cnn_results['cnn_confidence']
            )
            db.add(ai_result)
            db.commit()

            # Step 3: Generate Dual Reports IMMEDIATELY
            report_start = time.time()
            logger.info("[3/3] Generating streamlined reports (CNN + Vision AI only)...")

            # User Report
            user_report = self._generate_user_report(
                cnn_results, vision_findings, questionnaire_dict
            )

            # HCP Report
            hcp_report = self._generate_hcp_report(
                cnn_results, vision_findings, questionnaire_dict
            )
            report_gen_time = time.time() - report_start
            logger.info(f"⏱️  Reports generated in {report_gen_time:.2f}s")

            # Save reports IMMEDIATELY
            db_save_start = time.time()
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
            db_save_time = time.time() - db_save_start
            logger.success(f"Reports saved in {db_save_time:.2f}s")

            total_time = time.time() - parallel_start
            logger.success(f"✅ Multi-agent analysis complete for session: {session_id}")
            logger.info(f"⏱️  TOTAL TIME: {total_time:.1f}s (target: <120s)")
            logger.info(f"💰 Total cost estimate: ${(vision_response.cost or 0):.4f}")

        except Exception as e:
            logger.error(f"Error in multi-agent analysis pipeline: {e}")
            db.rollback()
            raise
        finally:
            # IMPORTANT: Close DB session created for background task
            db.close()

    def _generate_user_report(
        self, cnn_results: Dict, vision_findings: Dict, questionnaire: Dict
    ) -> Dict:
        """Generate user-friendly report from CNN + Vision AI results"""
        # Calculate CONSENSUS severity (same as HCP report for consistency)
        cnn_severity = cnn_results['severity_score']  # 0-100
        vision_iga = vision_findings.get("severity_assessment", {}).get("iga_score", 0)  # 0-4
        vision_severity_normalized = (vision_iga / 4.0) * 100  # Convert to 0-100 scale
        consensus_severity = (cnn_severity + vision_severity_normalized) / 2

        # Determine severity category from consensus (matches HCP report)
        if consensus_severity < 30:
            severity_cat = "Mild"
        elif consensus_severity < 60:
            severity_cat = "Moderate"
        else:
            severity_cat = "Severe"

        # Extract lesion metrics from vision_findings
        lesion_count = vision_findings.get("lesion_count", 0)
        erythema_pct = vision_findings.get("erythema_percentage", 0)

        return {
            "type": "user",
            "severity": severity_cat,
            "summary": f"Analysis complete. Your AD severity is {severity_cat.lower()}.",
            "key_findings": [
                f"Consensus Severity: {round(consensus_severity, 1)}/100",
                f"CNN Severity: {cnn_severity:.1f}/100",
                f"Vision AI IGA: {vision_iga}/4",
                f"Lesion Count: {lesion_count}",
                f"Erythema: {erythema_pct:.1f}%",
                f"Affected Area: {cnn_results['affected_area_pct']:.1f}%"
            ],
            "vision_analysis": vision_findings.get("assessment", "Vision AI analysis complete."),
            "recommendations": [
                "Continue daily moisturizer routine",
                "Consult with your dermatologist about treatment",
                "Track symptoms and flare triggers"
            ],
            "when_to_seek_help": "Contact your doctor if symptoms worsen or don't improve in 7-10 days."
        }

    def _generate_hcp_report(
        self, cnn_results: Dict, vision_findings: Dict, questionnaire: Dict
    ) -> Dict:
        """Generate HCP clinical report with CNN + Vision AI consensus values"""

        # CONSENSUS METRICS: Average overlapping attributes from CNN and Vision AI

        # 1. Severity consensus (normalize Vision AI IGA 0-4 to 0-100 scale)
        cnn_severity = cnn_results['severity_score']  # 0-100
        vision_iga = vision_findings.get("severity_assessment", {}).get("iga_score", 0)  # 0-4
        vision_severity_normalized = (vision_iga / 4.0) * 100  # Convert to 0-100 scale
        consensus_severity = (cnn_severity + vision_severity_normalized) / 2

        # 2. Affected area consensus
        cnn_affected_area = cnn_results['affected_area_pct']  # 0-100%
        vision_affected_area = vision_findings.get("severity_assessment", {}).get("affected_area_estimate", 0)
        consensus_affected_area = (cnn_affected_area + vision_affected_area) / 2

        # 3. Inflammation/Erythema consensus
        cnn_inflammation = cnn_results['inflammation_score']  # 0-100
        vision_erythema = vision_findings.get("clinical_findings", {}).get("erythema", {}).get("severity", 0)  # 0-3
        vision_erythema_normalized = (vision_erythema / 3.0) * 100  # Convert to 0-100 scale
        consensus_inflammation = (cnn_inflammation + vision_erythema_normalized) / 2

        # Determine severity category from consensus
        if consensus_severity < 30:
            severity_cat = "Mild"
        elif consensus_severity < 60:
            severity_cat = "Moderate"
        else:
            severity_cat = "Severe"

        # Generate SOAP note using consensus values
        soap_note = self._generate_soap_note(cnn_results, vision_findings, questionnaire)

        # Extract Vision AI-specific metrics
        lesion_count = vision_findings.get("lesion_count", 0)
        erythema_pct = vision_findings.get("erythema_percentage", 0)

        return {
            "type": "hcp",
            "integrated_assessment": {
                "consensus_severity": round(consensus_severity, 1),
                "consensus_affected_area": round(consensus_affected_area, 1),
                "consensus_inflammation": round(consensus_inflammation, 1),
                "severity_category": severity_cat,
                "cnn_severity": cnn_severity,
                "vision_severity_iga": vision_iga,
                "lesion_count": lesion_count,
                "erythema_percentage": erythema_pct
            },
            "soap_note": soap_note,
            "cnn_analysis": cnn_results,
            "vision_agent_findings": vision_findings,
            "rag_enhanced": True
        }

    def _generate_soap_note(
        self, cnn_results: Dict, vision_findings: Dict, questionnaire: Dict
    ) -> Dict:
        """Generate SOAP-formatted clinical note with severity-based treatment plan"""
        # Determine treatment plan based on CNN severity
        severity = cnn_results['severity_score']
        if severity < 30:
            plan = "Continue daily emollients. Monitor for changes. Follow-up as needed or if symptoms worsen."
        elif severity < 60:
            plan = "Increase emollient frequency. Consider low-potency topical corticosteroids for flares. Follow-up in 2-4 weeks."
        else:
            plan = "Intensive moisturizer regimen. Mid-to-high potency topical corticosteroids as directed. Consider adjunct therapy if insufficient response. Follow-up in 1-2 weeks or sooner if worsening."

        return {
            "subjective": f"Patient reports itch intensity {questionnaire.get('itch_intensity', 0)}/10. Sleep disturbance: {questionnaire.get('nights_sleep_disturbed', 0)}/7 nights. Primary location: {questionnaire.get('primary_location', 'unspecified')}.",
            "objective": f"CNN Analysis: Severity {cnn_results['severity_score']:.1f}/100, affected area {cnn_results['affected_area_pct']:.1f}%. Inflammation score: {cnn_results['inflammation_score']:.1f}. Vision AI: {vision_findings.get('lesion_count', 0)} lesions detected, erythema {vision_findings.get('erythema_percentage', 0):.1f}%.",
            "assessment": vision_findings.get("assessment", f"Atopic Dermatitis - Severity: {cnn_results['severity_score']:.1f}/100"),
            "plan": plan
        }


# Global instance
multiagent_analysis_service = MultiAgentAnalysisService()
