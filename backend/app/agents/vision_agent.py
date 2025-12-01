"""
Vision Agent - Analyzes skin images for Atopic Dermatitis
Uses Gemini 1.5 Flash (Vertex AI) or Qwen VLM (Together.AI)
"""

import base64
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from PIL import Image

from app.agents.base_agent import BaseAgent
from app.config.agent_config import VISION_AGENT_CONFIG
from app.prompts.vision_agent_prompts import (
    VISION_SYSTEM_PROMPT,
    VISION_ANALYSIS_PROMPT,
)
from app.rag.rag_service import rag_service

logger = logging.getLogger(__name__)


class ADVisionAgent(BaseAgent):
    """
    Specialized agent for analyzing AD skin images
    """

    def __init__(self):
        super().__init__(VISION_AGENT_CONFIG)

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {str(e)}")
            raise

    def _validate_image(self, image_path: str) -> Dict[str, Any]:
        """Validate image quality and format"""
        try:
            image = Image.open(image_path)

            width, height = image.size
            file_size = Path(image_path).stat().st_size / (1024 * 1024)  # MB

            validation = {
                "valid": True,
                "width": width,
                "height": height,
                "file_size_mb": file_size,
                "format": image.format,
                "issues": []
            }

            # Check image dimensions
            if width < 224 or height < 224:
                validation["issues"].append("Image resolution too low (minimum 224x224)")

            # Check file size
            if file_size > 10:
                validation["issues"].append("Image file size too large (>10MB)")

            # Check format
            if image.format not in ["JPEG", "PNG", "JPG"]:
                validation["issues"].append(f"Unsupported format: {image.format}")

            validation["valid"] = len(validation["issues"]) == 0

            return validation

        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Image validation failed: {str(e)}"]
            }

    async def analyze_image(
        self,
        image_path: str,
        body_area: Optional[str] = None,
        symptoms: Optional[str] = None,
        has_history: bool = False,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a single image for AD assessment

        Args:
            image_path: Path to image file
            body_area: Anatomical location
            symptoms: Patient-reported symptoms
            has_history: Known AD history
            use_rag: Whether to augment with RAG clinical knowledge

        Returns:
            VLM analysis results with clinical findings
        """
        # Validate image
        validation = self._validate_image(image_path)
        if not validation["valid"]:
            logger.warning(f"Image quality issues: {validation['issues']}")

        # Prepare base prompt
        user_prompt = VISION_ANALYSIS_PROMPT.format(
            body_area=body_area or "Not specified",
            symptoms=symptoms or "Not specified",
            has_history=str(has_history)
        )

        # Augment with RAG clinical knowledge
        if use_rag:
            clinical_query = f"atopic dermatitis differential diagnosis {body_area or ''} {symptoms or ''}"
            user_prompt = rag_service.augment_prompt_with_knowledge(
                base_prompt=user_prompt,
                clinical_query=clinical_query,
                top_k=2  # Top 2 most relevant knowledge sources
            )
            logger.info("Augmented vision prompt with RAG clinical knowledge")

        # Encode image
        image_b64 = self._encode_image(image_path)

        # Create message with image (format depends on provider)
        from app.config.agent_config import ModelProvider

        if self.config.provider == ModelProvider.VERTEX_AI:
            # Gemini format
            messages = [
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ]
        else:
            # Together.AI format (OpenAI-compatible)
            messages = [
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ]

        # Invoke LLM
        response = await self.llm.ainvoke(messages)

        # Parse JSON response
        try:
            analysis = self._parse_json_response(response.content)
            analysis["image_validation"] = validation
            return analysis
        except Exception as e:
            logger.error(f"Failed to parse vision response: {str(e)}")
            raise

    async def _process_implementation(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main processing method called by base class

        Expected input_data:
        {
            "image_path": str,
            "body_area": str (optional),
            "symptoms": str (optional),
            "has_history": bool
        }
        """
        image_path = input_data.get("image_path")
        if not image_path:
            raise ValueError("No image path provided")

        body_area = input_data.get("body_area")
        symptoms = input_data.get("symptoms")
        has_history = input_data.get("has_history", False)

        # Perform VLM analysis
        result = await self.analyze_image(
            image_path=image_path,
            body_area=body_area,
            symptoms=symptoms,
            has_history=has_history
        )

        # Extract confidence score
        confidence = self._extract_confidence(result)

        return {
            "data": result,
            "confidence": confidence,
            "tokens_used": {
                "input": len(str(input_data)) // 4,  # Rough estimate
                "output": len(str(result)) // 4
            }
        }

    def _extract_confidence(self, result: Dict[str, Any]) -> float:
        """Extract average confidence from analysis results"""
        if "clinical_findings" in result:
            findings = result["clinical_findings"]
            confidences = []

            for key in ["erythema", "edema_induration", "excoriation", "lichenification"]:
                if key in findings and "confidence" in findings[key]:
                    confidences.append(findings[key]["confidence"] / 100.0)

            return sum(confidences) / len(confidences) if confidences else 0.5

        if "severity_assessment" in result:
            return result["severity_assessment"].get("confidence", 50) / 100.0

        return 0.5


# Global instance
ad_vision_agent = ADVisionAgent()
