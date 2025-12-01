"""
Base Agent Class for AD Assessment
Supports GCP Vertex AI (Gemini) and Together.AI
"""

import json
import time
import logging
import os
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: float
    tokens_used: Optional[Dict[str, int]] = None
    cost: Optional[float] = None


class BaseAgent(ABC):
    """
    Base class for all AD assessment agents
    Supports Vertex AI Gemini and Together.AI models
    """

    def __init__(self, config):
        self.config = config
        self.llm = self._initialize_llm()

        logger.info(f"Initialized {config.name} with model {config.model}")

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        from app.config.agent_config import ModelProvider

        if self.config.provider == ModelProvider.VERTEX_AI:
            # Use Google Vertex AI (Gemini)
            try:
                from langchain_google_vertexai import ChatVertexAI

                return ChatVertexAI(
                    model_name=self.config.model,
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                    project=os.getenv("GCP_PROJECT_ID", "total-furnace-288818"),
                    location=os.getenv("GCP_REGION", "us-central1"),
                )
            except ImportError:
                logger.error("langchain-google-vertexai not installed. Install: pip install langchain-google-vertexai")
                raise

        elif self.config.provider == ModelProvider.TOGETHER:
            # Use Together.AI
            try:
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout_seconds,
                    base_url="https://api.together.xyz/v1",
                    api_key=os.getenv("TOGETHER_API_KEY"),
                )
            except ImportError:
                logger.error("langchain-openai not installed")
                raise
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks"""
        try:
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Content: {content[:500]}")
            raise

    async def _invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> str:
        """Invoke LLM with system and user messages"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = await self.llm.ainvoke(messages)
        return response.content

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for this agent's operation"""
        input_cost = (input_tokens / 1_000_000) * self.config.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.config.cost_per_1m_output
        return input_cost + output_cost

    @abstractmethod
    async def _process_implementation(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Abstract method that each agent must implement
        Contains the core logic for that agent
        """
        pass

    async def process(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> AgentResponse:
        """
        Main entry point for agent processing
        Handles timing, error handling, and metrics
        """
        start_time = time.time()

        try:
            result = await self._process_implementation(input_data, **kwargs)

            processing_time = time.time() - start_time

            return AgentResponse(
                success=True,
                data=result.get("data"),
                confidence=result.get("confidence"),
                processing_time=processing_time,
                tokens_used=result.get("tokens_used"),
                cost=self.calculate_cost(
                    result.get("tokens_used", {}).get("input", 0),
                    result.get("tokens_used", {}).get("output", 0)
                )
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Agent {self.config.name} failed: {str(e)}")

            return AgentResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
