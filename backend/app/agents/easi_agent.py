"""
EASI Scoring Agent - Calculates EASI scores and provides clinical reasoning
Modeled after Psoriasis PASI reasoning agent
"""

import logging
from typing import Dict, Any, Optional, List

from app.agents.base_agent import BaseAgent
from app.config.agent_config import EASI_AGENT_CONFIG
from app.prompts.easi_agent_prompts import (
    EASI_SYSTEM_PROMPT,
    EASI_CALCULATION_PROMPT,
    TREATMENT_RECOMMENDATION_PROMPT,
    PROGRESSION_ANALYSIS_PROMPT
)
from app.rag.rag_service import rag_service

logger = logging.getLogger(__name__)


class EASIReasoningAgent(BaseAgent):
    """
    Specialized agent for EASI calculation and medical reasoning
    """

    def __init__(self):
        super().__init__(EASI_AGENT_CONFIG)

    async def calculate_easi(
        self,
        vision_findings: Dict[str, Any],
        questionnaire_data: Dict[str, Any],
        body_regions: Optional[Dict[str, Any]] = None,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate EASI score following official methodology

        Args:
            vision_findings: VLM analysis results
            questionnaire_data: 12-question responses
            body_regions: Optional specific region data
            use_rag: Whether to augment with RAG clinical knowledge

        Returns:
            Complete EASI calculation with reasoning
        """
        prompt = EASI_CALCULATION_PROMPT.format(
            vision_findings=str(vision_findings),
            questionnaire_data=str(questionnaire_data),
            body_regions=str(body_regions or {})
        )

        # Augment with EASI scoring guidelines from RAG
        if use_rag:
            prompt = rag_service.augment_prompt_with_knowledge(
                base_prompt=prompt,
                clinical_query="EASI scoring methodology official criteria",
                top_k=1  # Just the EASI scoring guide
            )
            logger.info("Augmented EASI prompt with official scoring guidelines")

        response = await self._invoke_llm(
            system_prompt=EASI_SYSTEM_PROMPT,
            user_message=prompt
        )

        easi_result = self._parse_json_response(response)

        # Validate EASI calculation
        self._validate_easi_calculation(easi_result)

        return easi_result

    def _validate_easi_calculation(self, easi_result: Dict[str, Any]) -> None:
        """Validate EASI calculation is within expected ranges"""
        easi_calc = easi_result.get("easi_calculation", {})
        total_easi = easi_calc.get("total_easi", 0)

        # Handle None values safely
        if total_easi is None:
            total_easi = 0
            logger.warning("total_easi is None, defaulting to 0")

        if not (0 <= total_easi <= 72):
            logger.warning(f"EASI score {total_easi} outside valid range [0-72]")

        # Validate regional scores
        for region in ["head_neck", "trunk", "upper_limbs", "lower_limbs"]:
            if region in easi_calc:
                region_data = easi_calc[region]

                # Validate clinical sign scores (0-3)
                for sign in ["erythema", "induration", "excoriation", "lichenification"]:
                    score = region_data.get(sign, 0)
                    # Handle None values safely
                    if score is None:
                        score = 0
                    if not (0 <= score <= 3):
                        logger.warning(f"{region} {sign} score {score} outside [0-3]")

                # Validate area score (0-6)
                area_score = region_data.get("area_score", 0)
                # Handle None values safely
                if area_score is None:
                    area_score = 0
                if not (0 <= area_score <= 6):
                    logger.warning(f"{region} area_score {area_score} outside [0-6]")

                # Validate regional EASI calculation
                sum_signs = sum([
                    region_data.get(sign, 0) if region_data.get(sign) is not None else 0
                    for sign in ["erythema", "induration", "excoriation", "lichenification"]
                ])

                sum_of_signs = region_data.get("sum_of_signs")
                if sum_of_signs is not None and sum_signs != sum_of_signs:
                    logger.warning(f"{region}: sum_of_signs mismatch")

    async def recommend_treatment(
        self,
        easi_score: float,
        severity: str,
        affected_regions: List[str],
        questionnaire_data: Dict[str, Any],
        current_treatments: Optional[List[str]] = None,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Recommend treatment approach based on EASI assessment

        Args:
            easi_score: Calculated EASI score
            severity: Severity classification
            affected_regions: List of affected body regions
            questionnaire_data: Patient questionnaire responses
            current_treatments: Current treatment regimen
            use_rag: Whether to augment with RAG clinical knowledge

        Returns:
            Treatment recommendations
        """
        prompt = TREATMENT_RECOMMENDATION_PROMPT.format(
            easi_score=easi_score,
            severity=severity,
            affected_regions=", ".join(affected_regions),
            questionnaire_data=str(questionnaire_data),
            current_treatments=", ".join(current_treatments or ["None"])
        )

        # Augment with treatment guidelines from RAG
        if use_rag:
            prompt = rag_service.augment_prompt_with_knowledge(
                base_prompt=prompt,
                clinical_query=f"atopic dermatitis treatment {severity} EASI {easi_score}",
                top_k=2  # Treatment guidelines + severity-specific recommendations
            )
            logger.info("Augmented treatment prompt with clinical guidelines")

        response = await self._invoke_llm(
            system_prompt=EASI_SYSTEM_PROMPT,
            user_message=prompt
        )

        return self._parse_json_response(response)

    async def analyze_progression(
        self,
        current_data: Dict[str, Any],
        historical_assessments: List[Dict[str, Any]],
        timeline: str
    ) -> Dict[str, Any]:
        """
        Analyze disease progression over time

        Args:
            current_data: Current EASI assessment
            historical_assessments: Previous assessments
            timeline: Time period analyzed

        Returns:
            Progression analysis
        """
        prompt = PROGRESSION_ANALYSIS_PROMPT.format(
            current_data=str(current_data),
            historical_assessments=str(historical_assessments),
            timeline=timeline
        )

        response = await self._invoke_llm(
            system_prompt=EASI_SYSTEM_PROMPT,
            user_message=prompt
        )

        return self._parse_json_response(response)

    async def _process_implementation(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main processing method called by base class

        Expected input_data:
        {
            "vision_findings": {...},
            "questionnaire_data": {...},
            "body_regions": {...} (optional),
            "action": "calculate_easi" | "recommend_treatment" | "analyze_progression"
        }
        """
        action = input_data.get("action", "calculate_easi")

        if action == "calculate_easi":
            result = await self.calculate_easi(
                vision_findings=input_data.get("vision_findings", {}),
                questionnaire_data=input_data.get("questionnaire_data", {}),
                body_regions=input_data.get("body_regions")
            )

        elif action == "recommend_treatment":
            result = await self.recommend_treatment(
                easi_score=input_data.get("easi_score", 0),
                severity=input_data.get("severity", "Unknown"),
                affected_regions=input_data.get("affected_regions", []),
                questionnaire_data=input_data.get("questionnaire_data", {}),
                current_treatments=input_data.get("current_treatments")
            )

        elif action == "analyze_progression":
            result = await self.analyze_progression(
                current_data=input_data.get("current_data", {}),
                historical_assessments=input_data.get("historical_assessments", []),
                timeline=input_data.get("timeline", "Unknown")
            )

        else:
            raise ValueError(f"Unknown action: {action}")

        return {
            "data": result,
            "confidence": 0.9,  # High confidence for structured calculation
            "tokens_used": {
                "input": len(str(input_data)) // 4,
                "output": len(str(result)) // 4
            }
        }


# Global instance
easi_agent = EASIReasoningAgent()
