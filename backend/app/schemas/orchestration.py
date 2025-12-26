"""
Orchestration schemas for complete screening pipeline.

This module defines the structure for end-to-end candidate screening,
including batch processing and status tracking.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of a screening job."""
    PENDING = "pending"           # Queued, not started
    PARSING = "parsing"           # Parsing documents
    EXTRACTING = "extracting"     # AI extraction (Phases 4-5)
    MATCHING = "matching"         # Skill matching (Phase 6)
    SCORING = "scoring"           # Decision making (Phase 7)
    GENERATING_FEEDBACK = "generating_feedback"  # Feedback generation (Phase 8)
    COMPLETED = "completed"       # Successfully finished
    FAILED = "failed"             # Error occurred


class ScreeningResult(BaseModel):
    """Complete screening result for one candidate."""
    
    # Candidate info
    candidate_name: str
    resume_file_id: str
    job_file_id: str
    
    # Results from each phase
    overall_score: float = Field(ge=0.0, le=100.0)
    decision: str = Field(description="HIRE/MAYBE/REJECT")
    confidence: str = Field(description="HIGH/MEDIUM/LOW")
    
    # Key insights
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    
    # Feedback
    feedback_message: Optional[str] = None
    
    # Metadata
    requires_human_review: bool
    review_priority: str
    processing_time_ms: float
    cost_usd: float = Field(description="Total cost for this screening")


class ScreeningJob(BaseModel):
    """Status and result of a screening job."""
    
    job_id: str = Field(description="Unique job identifier")
    status: JobStatus
    
    # Input
    resume_file_id: str
    job_file_id: str
    
    # Progress tracking
    current_phase: Optional[str] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    
    # Result (populated when completed)
    result: Optional[ScreeningResult] = None
    
    # Error tracking
    error_message: Optional[str] = None
    error_phase: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SingleScreeningRequest(BaseModel):
    """Request to screen a single candidate."""
    
    resume_file_id: str = Field(description="Resume file UUID")
    job_file_id: str = Field(description="Job description file UUID")
    
    # Optional overrides
    custom_thresholds: Optional[Dict[str, float]] = Field(
        default=None,
        description="Custom scoring thresholds"
    )
    include_feedback: bool = Field(
        default=True,
        description="Generate candidate feedback"
    )
    include_score_in_feedback: bool = Field(
        default=False,
        description="Include numerical score in feedback"
    )


class SingleScreeningResponse(BaseModel):
    """Response from single candidate screening."""
    
    success: bool
    job_id: str = Field(description="Job ID for tracking")
    result: Optional[ScreeningResult] = None
    error: Optional[str] = None


class BatchScreeningRequest(BaseModel):
    """Request to screen multiple candidates."""
    
    job_file_id: str = Field(description="Single job description for all candidates")
    resume_file_ids: List[str] = Field(
        description="List of resume file UUIDs",
        min_length=1,
        max_length=100  # Limit batch size
    )
    
    # Optional overrides
    custom_thresholds: Optional[Dict[str, float]] = None
    include_feedback: bool = Field(default=True)
    include_score_in_feedback: bool = Field(default=False)


class BatchScreeningResponse(BaseModel):
    """Response from batch screening."""
    
    success: bool
    batch_id: str = Field(description="Batch identifier")
    total_candidates: int
    
    # Job tracking
    job_ids: List[str] = Field(
        default_factory=list,
        description="Individual job IDs for progress tracking"
    )
    
    # Quick summary
    estimated_completion_seconds: float = Field(
        description="Estimated time to complete all screenings"
    )
    estimated_cost_usd: float = Field(
        description="Estimated total cost"
    )
    
    error: Optional[str] = None


class BatchStatusRequest(BaseModel):
    """Request to check batch screening status."""
    
    batch_id: str = Field(description="Batch identifier to check")


class BatchStatusResponse(BaseModel):
    """Status of a batch screening operation."""
    
    success: bool
    batch_id: str
    
    # Overall progress
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    pending_jobs: int
    progress_percent: float = Field(ge=0.0, le=100.0)
    
    # Individual job statuses
    jobs: List[ScreeningJob] = Field(default_factory=list)
    
    # Results (for completed jobs)
    results: List[ScreeningResult] = Field(default_factory=list)
    
    # Summary statistics
    decisions_summary: Optional[Dict[str, int]] = Field(
        default=None,
        description="Count of HIRE/MAYBE/REJECT decisions"
    )
    
    error: Optional[str] = None


class ScreeningConfig(BaseModel):
    """Configuration for screening operations."""
    
    # Thresholds
    hire_threshold: float = Field(default=75.0, ge=0.0, le=100.0)
    reject_threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    
    # Flags
    generate_feedback: bool = Field(default=True)
    include_scores: bool = Field(default=False)
    
    # Performance
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_seconds: int = Field(default=30, ge=10, le=120)
