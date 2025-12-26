"""
Feedback schemas for candidate communication.

This module defines the structure of feedback sent to candidates
after the screening process.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class FeedbackTone(str, Enum):
    """Tone of feedback delivery."""
    ENCOURAGING = "encouraging"      # For HIRE - enthusiastic
    CONSTRUCTIVE = "constructive"    # For MAYBE - balanced
    SUPPORTIVE = "supportive"        # For REJECT - empathetic


class FeedbackSection(BaseModel):
    """A section of feedback content."""
    title: str = Field(description="Section heading")
    content: str = Field(description="Section text content")


class CandidateFeedback(BaseModel):
    """
    Complete feedback package for a candidate.
    
    This is the output of Phase 8 - human-readable feedback
    generated from the structured DecisionResult from Phase 7.
    """
    
    # Decision context
    decision: str = Field(description="HIRE/MAYBE/REJECT")
    overall_score: float = Field(description="Match score from Phase 6")
    
    # Feedback content
    opening_message: str = Field(
        description="Personalized greeting and decision statement"
    )
    
    strengths_summary: str = Field(
        description="What the candidate did well"
    )
    
    areas_for_improvement: Optional[str] = Field(
        default=None,
        description="Skills/areas to develop (for MAYBE/REJECT)"
    )
    
    detailed_feedback: List[FeedbackSection] = Field(
        default_factory=list,
        description="Structured feedback sections"
    )
    
    skill_recommendations: List[str] = Field(
        default_factory=list,
        description="Specific skills to learn/improve"
    )
    
    next_steps: List[str] = Field(
        description="What happens next in the process"
    )
    
    closing_message: str = Field(
        description="Encouraging closing statement"
    )
    
    # Metadata
    tone: FeedbackTone = Field(description="Overall tone of feedback")
    estimated_read_time_minutes: int = Field(
        default=3,
        description="How long to read this feedback"
    )


class FeedbackRequest(BaseModel):
    """Request to generate feedback."""
    resume_file_id: str = Field(description="Resume file ID")
    job_file_id: str = Field(description="Job description file ID")
    custom_thresholds: Optional[dict] = Field(
        default=None,
        description="Optional custom scoring thresholds"
    )
    include_score_details: bool = Field(
        default=False,
        description="Include numerical scores in feedback"
    )


class FeedbackResponse(BaseModel):
    """Response from feedback generation."""
    success: bool
    feedback: Optional[CandidateFeedback] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "feedback": {
                    "decision": "MAYBE",
                    "overall_score": 68.5,
                    "opening_message": "Thank you for applying to the Senior ML Engineer position...",
                    "strengths_summary": "You have strong Python skills and relevant experience...",
                    "areas_for_improvement": "We'd like to see more experience with Docker and Kubernetes...",
                    "skill_recommendations": [
                        "Docker and Kubernetes for container orchestration",
                        "AWS services (EC2, S3, Lambda)"
                    ],
                    "next_steps": [
                        "We'll schedule a phone screen to discuss your background",
                        "Be prepared to discuss your ML project experience"
                    ],
                    "closing_message": "We're excited about your potential and look forward to speaking with you!",
                    "tone": "constructive"
                },
                "processing_time_ms": 2500.0
            }
        }
