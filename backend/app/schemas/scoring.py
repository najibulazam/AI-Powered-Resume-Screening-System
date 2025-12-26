"""
Scoring schemas for decision-making.

This module defines the structure of scoring decisions and results.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Decision(str, Enum):
    """Hiring decision categories."""
    HIRE = "hire"          # Strong match - recommend hiring
    MAYBE = "maybe"        # Borderline - needs review
    REJECT = "reject"      # Weak match - not recommended


class ConfidenceLevel(str, Enum):
    """Decision confidence levels."""
    HIGH = "high"          # Very clear decision (near thresholds)
    MEDIUM = "medium"      # Moderate confidence
    LOW = "low"            # Close call (near boundaries)


class ThresholdConfig(BaseModel):
    """Configurable scoring thresholds."""
    hire_threshold: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
        description="Minimum score for HIRE decision"
    )
    reject_threshold: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Maximum score for REJECT decision (inclusive)"
    )
    
    def validate(self):
        """Ensure thresholds are logical."""
        if self.reject_threshold >= self.hire_threshold:
            raise ValueError(
                f"reject_threshold ({self.reject_threshold}) must be less than "
                f"hire_threshold ({self.hire_threshold})"
            )


class DecisionReasoning(BaseModel):
    """Detailed reasoning for a decision."""
    primary_factors: List[str] = Field(
        description="Key factors influencing the decision"
    )
    supporting_evidence: List[str] = Field(
        description="Supporting data points"
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="Potential concerns or red flags"
    )
    edge_cases: List[str] = Field(
        default_factory=list,
        description="Special circumstances to consider"
    )


class DecisionResult(BaseModel):
    """Complete scoring decision with reasoning."""
    decision: Decision = Field(
        description="Final hiring decision"
    )
    confidence: ConfidenceLevel = Field(
        description="Confidence level in this decision"
    )
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
        description="The match score from Phase 6"
    )
    thresholds_used: ThresholdConfig = Field(
        description="Thresholds applied for this decision"
    )
    reasoning: DecisionReasoning = Field(
        description="Detailed reasoning for the decision"
    )
    requires_human_review: bool = Field(
        description="Whether this candidate needs manual review"
    )
    review_priority: str = Field(
        description="Priority level for review (high/medium/low)"
    )
    next_steps: List[str] = Field(
        description="Recommended next actions"
    )


class ScoringRequest(BaseModel):
    """Request to score a candidate."""
    resume_file_id: str = Field(
        description="UUID of the uploaded resume file"
    )
    job_file_id: str = Field(
        description="UUID of the uploaded job description file"
    )
    custom_thresholds: Optional[ThresholdConfig] = Field(
        default=None,
        description="Optional custom thresholds (uses defaults if not provided)"
    )


class ScoringResponse(BaseModel):
    """Response from scoring a candidate."""
    success: bool
    decision_result: Optional[DecisionResult] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "decision_result": {
                    "decision": "maybe",
                    "confidence": "medium",
                    "overall_score": 68.5,
                    "thresholds_used": {
                        "hire_threshold": 75.0,
                        "reject_threshold": 50.0
                    },
                    "reasoning": {
                        "primary_factors": [
                            "Score of 68.5 falls in MAYBE range (50-75)",
                            "Strong technical skills but missing some key requirements"
                        ],
                        "supporting_evidence": [
                            "70% required skills matched",
                            "Experience meets requirements",
                            "Education level appropriate"
                        ],
                        "concerns": [
                            "Missing Docker/Kubernetes experience",
                            "No cloud platform experience"
                        ]
                    },
                    "requires_human_review": True,
                    "review_priority": "medium",
                    "next_steps": [
                        "Schedule phone screen to assess missing skills",
                        "Ask about Docker/Kubernetes learning timeline"
                    ]
                },
                "processing_time_ms": 2.5
            }
        }
