"""
AD Multi-Agent System Configuration
Using GCP Vertex AI Gemini models for cost-effective deployment
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ModelProvider(str, Enum):
    VERTEX_AI = "vertex_ai"  # GCP Vertex AI (Gemini)
    TOGETHER = "together"     # Together.ai alternative


class AgentRole(str, Enum):
    VISION = "vision"
    REPORT = "report"


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    name: str
    role: AgentRole
    model: str
    provider: ModelProvider
    temperature: float = 0.3
    max_tokens: int = 4000
    cost_per_1m_input: float
    cost_per_1m_output: float
    retry_attempts: int = 3
    timeout_seconds: int = 60
    description: str


# ============================================================================
# OPTION 1: GCP Vertex AI Gemini Models
# ============================================================================

# Gemini 1.5 Pro - RECOMMENDED for best quality
VISION_AGENT_CONFIG_GEMINI_PRO = AgentConfig(
    name="AD Vision Specialist (Gemini Pro)",
    role=AgentRole.VISION,
    model="gemini-1.5-pro-002",  # Best quality for medical imaging
    provider=ModelProvider.VERTEX_AI,
    temperature=0.2,
    max_tokens=8000,
    cost_per_1m_input=1.25,    # $1.25 per 1M tokens
    cost_per_1m_output=5.00,   # $5.00 per 1M tokens
    retry_attempts=3,
    timeout_seconds=45,
    description="Analyzes AD using Gemini 1.5 Pro - best quality for medical imaging, RAG-enabled"
)

# Gemini 2.0 Flash - Latest experimental model
VISION_AGENT_CONFIG_GEMINI_2_FLASH = AgentConfig(
    name="AD Vision Specialist (Gemini 2.0)",
    role=AgentRole.VISION,
    model="gemini-2.0-flash-exp",  # Experimental latest model
    provider=ModelProvider.VERTEX_AI,
    temperature=0.2,
    max_tokens=8000,
    cost_per_1m_input=0.10,    # Cheap
    cost_per_1m_output=0.40,
    retry_attempts=3,
    timeout_seconds=30,
    description="Latest Gemini 2.0 Flash experimental - fast and improved"
)

# Gemini 1.5 Flash - Budget option
VISION_AGENT_CONFIG_GEMINI_FLASH = AgentConfig(
    name="AD Vision Specialist (Flash)",
    role=AgentRole.VISION,
    model="gemini-1.5-flash-002",
    provider=ModelProvider.VERTEX_AI,
    temperature=0.2,
    max_tokens=4000,
    cost_per_1m_input=0.075,
    cost_per_1m_output=0.30,
    retry_attempts=3,
    timeout_seconds=30,
    description="Budget option - Gemini 1.5 Flash"
)

# Default: Use Pro for best quality
VISION_AGENT_CONFIG_GEMINI = VISION_AGENT_CONFIG_GEMINI_PRO

REPORT_AGENT_CONFIG_GEMINI = AgentConfig(
    name="AD Report Generator",
    role=AgentRole.REPORT,
    model="gemini-1.5-flash-002",
    provider=ModelProvider.VERTEX_AI,
    temperature=0.4,  # Slightly creative for patient-friendly language
    max_tokens=2000,
    cost_per_1m_input=0.075,
    cost_per_1m_output=0.30,
    retry_attempts=2,
    timeout_seconds=20,
    description="Generates dual reports (user + HCP) using Gemini 1.5 Flash"
)


# ============================================================================
# OPTION 2: Together.AI (Alternative - Open Source)
# ============================================================================

VISION_AGENT_CONFIG_TOGETHER = AgentConfig(
    name="AD Vision Specialist",
    role=AgentRole.VISION,
    model="Qwen/Qwen2.5-VL-7B-Instruct",  # Smaller than psoriasis's 72B
    provider=ModelProvider.TOGETHER,
    temperature=0.2,
    max_tokens=4000,
    cost_per_1m_input=0.10,   # Cheaper than 72B model
    cost_per_1m_output=0.10,
    retry_attempts=3,
    timeout_seconds=45,
    description="Analyzes AD skin images using Qwen 2.5 VL 7B"
)

REPORT_AGENT_CONFIG_TOGETHER = AgentConfig(
    name="AD Report Generator",
    role=AgentRole.REPORT,
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    provider=ModelProvider.TOGETHER,
    temperature=0.4,
    max_tokens=2000,
    cost_per_1m_input=0.88,
    cost_per_1m_output=0.88,
    retry_attempts=2,
    timeout_seconds=30,
    description="Generates dual reports using Llama 3.3 70B"
)


# ============================================================================
# Active Configuration (Toggle between providers)
# ============================================================================

USE_VERTEX_AI = True  # Set to False to use Together.AI

if USE_VERTEX_AI:
    VISION_AGENT_CONFIG = VISION_AGENT_CONFIG_GEMINI
    REPORT_AGENT_CONFIG = REPORT_AGENT_CONFIG_GEMINI
else:
    VISION_AGENT_CONFIG = VISION_AGENT_CONFIG_TOGETHER
    REPORT_AGENT_CONFIG = REPORT_AGENT_CONFIG_TOGETHER


# Agent registry
AGENT_REGISTRY: Dict[AgentRole, AgentConfig] = {
    AgentRole.VISION: VISION_AGENT_CONFIG,
    AgentRole.REPORT: REPORT_AGENT_CONFIG,
}


class WorkflowConfig(BaseModel):
    """Configuration for the AD assessment workflow"""
    enable_vision_agent: bool = True
    enable_report_agent: bool = True
    enable_cnn_integration: bool = True  # Combine CNN + VLM results

    # Quality control
    require_confidence_threshold: float = 0.7
    human_review_threshold: float = 0.5

    # Performance
    max_concurrent_agents: int = 2
    workflow_timeout_seconds: int = 120


DEFAULT_WORKFLOW_CONFIG = WorkflowConfig()


class CostEstimator:
    """Estimate costs for agent operations"""

    @staticmethod
    def estimate_cost(
        agent_config: AgentConfig,
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> float:
        """Calculate estimated cost for an agent operation"""
        input_cost = (estimated_input_tokens / 1_000_000) * agent_config.cost_per_1m_input
        output_cost = (estimated_output_tokens / 1_000_000) * agent_config.cost_per_1m_output
        return input_cost + output_cost

    @staticmethod
    def estimate_ad_assessment_cost(
        num_images: int = 1,
        use_vertex_ai: bool = True
    ) -> Dict[str, float]:
        """Estimate total cost for a complete AD assessment"""

        # Token estimates
        vision_input = 4000 + (num_images * 2000)  # Prompt + images
        vision_output = 1500

        report_input = 2500
        report_output = 1500

        if use_vertex_ai:
            vision_cost = CostEstimator.estimate_cost(
                VISION_AGENT_CONFIG_GEMINI, vision_input, vision_output
            )
            report_cost = CostEstimator.estimate_cost(
                REPORT_AGENT_CONFIG_GEMINI, report_input, report_output
            )
        else:
            vision_cost = CostEstimator.estimate_cost(
                VISION_AGENT_CONFIG_TOGETHER, vision_input, vision_output
            )
            report_cost = CostEstimator.estimate_cost(
                REPORT_AGENT_CONFIG_TOGETHER, report_input, report_output
            )

        costs = {
            "vision": vision_cost,
            "report": report_cost,
            "total": vision_cost + report_cost
        }

        return costs


def get_agent_config(role: AgentRole) -> AgentConfig:
    """Get configuration for a specific agent role"""
    return AGENT_REGISTRY[role]


def estimate_cost_for_ad_assessment(**kwargs) -> Dict[str, float]:
    """Convenience function to estimate assessment cost"""
    return CostEstimator.estimate_ad_assessment_cost(**kwargs)


# Example usage and cost estimation
if __name__ == "__main__":
    print("=== AD Multi-Agent System Configuration ===\n")

    for role, config in AGENT_REGISTRY.items():
        print(f"{config.name} ({role.value})")
        print(f"  Model: {config.model}")
        print(f"  Provider: {config.provider.value}")
        print(f"  Cost: ${config.cost_per_1m_input}/1M input, ${config.cost_per_1m_output}/1M output")
        print()

    # Cost estimation
    print("=== Cost Estimation (Gemini 1.5 Flash) ===\n")

    scenarios = [
        {"name": "Single Image Assessment", "num_images": 1, "use_vertex_ai": True},
        {"name": "Multiple Images (3)", "num_images": 3, "use_vertex_ai": True},
        {"name": "Together.AI Alternative", "num_images": 1, "use_vertex_ai": False},
    ]

    for scenario in scenarios:
        name = scenario.pop("name")
        costs = estimate_cost_for_ad_assessment(**scenario)
        print(f"{name}:")
        print(f"  Vision Agent: ${costs['vision']:.6f}")
        print(f"  Report Agent: ${costs['report']:.6f}")
        print(f"  TOTAL: ${costs['total']:.6f}")
        print()
