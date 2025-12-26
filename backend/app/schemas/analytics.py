"""
Analytics schemas for aggregated screening data.

This module defines structures for dashboard analytics, reports,
and insights derived from multiple screening operations.
"""

from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TimeRange(str, Enum):
    """Time range for analytics queries."""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"


class DecisionStats(BaseModel):
    """Statistics about hiring decisions."""
    
    total_candidates: int = Field(ge=0, description="Total candidates screened")
    hire_count: int = Field(ge=0, description="Number of HIRE decisions")
    maybe_count: int = Field(ge=0, description="Number of MAYBE decisions")
    reject_count: int = Field(ge=0, description="Number of REJECT decisions")
    
    hire_percent: float = Field(ge=0.0, le=100.0, description="% of candidates hired")
    maybe_percent: float = Field(ge=0.0, le=100.0, description="% of maybes")
    reject_percent: float = Field(ge=0.0, le=100.0, description="% rejected")
    
    avg_score: float = Field(ge=0.0, le=100.0, description="Average match score")
    median_score: float = Field(ge=0.0, le=100.0, description="Median match score")
    
    human_review_required: int = Field(ge=0, description="Candidates needing review")
    human_review_percent: float = Field(ge=0.0, le=100.0, description="% needing review")


class SkillGapAnalysis(BaseModel):
    """Analysis of most common missing skills."""
    
    skill_name: str = Field(description="Name of the skill")
    gap_frequency: int = Field(ge=0, description="How many candidates missing this")
    gap_percent: float = Field(ge=0.0, le=100.0, description="% of candidates missing")
    priority: str = Field(description="HIGH/MEDIUM/LOW based on frequency")
    
    # Context
    typical_in_hires: bool = Field(
        default=False,
        description="Is this skill present in most HIRE candidates?"
    )
    typical_in_rejects: bool = Field(
        default=False,
        description="Is this skill missing in most REJECT candidates?"
    )


class CostAnalysis(BaseModel):
    """Cost tracking and analysis."""
    
    total_cost_usd: float = Field(ge=0.0, description="Total spending")
    cost_per_candidate: float = Field(ge=0.0, description="Average cost per screening")
    
    # Breakdown by phase
    resume_parsing_cost: float = Field(ge=0.0, description="Cost for Phase 4")
    job_parsing_cost: float = Field(ge=0.0, description="Cost for Phase 5")
    feedback_cost: float = Field(ge=0.0, description="Cost for Phase 8")
    
    # Projections
    estimated_monthly_cost: float = Field(ge=0.0, description="Monthly projection")
    estimated_annual_cost: float = Field(ge=0.0, description="Annual projection")


class PerformanceMetrics(BaseModel):
    """Performance and timing metrics."""
    
    total_screenings: int = Field(ge=0, description="Total completed screenings")
    
    avg_processing_time_ms: float = Field(ge=0.0, description="Average time per screening")
    median_processing_time_ms: float = Field(ge=0.0, description="Median processing time")
    min_processing_time_ms: float = Field(ge=0.0, description="Fastest screening")
    max_processing_time_ms: float = Field(ge=0.0, description="Slowest screening")
    
    # Phase breakdown
    avg_parsing_time_ms: float = Field(ge=0.0, description="Avg parsing time")
    avg_extraction_time_ms: float = Field(ge=0.0, description="Avg AI extraction")
    avg_matching_time_ms: float = Field(ge=0.0, description="Avg matching time")
    avg_scoring_time_ms: float = Field(ge=0.0, description="Avg scoring time")
    avg_feedback_time_ms: float = Field(ge=0.0, description="Avg feedback time")
    
    # Success rate
    success_rate: float = Field(ge=0.0, le=100.0, description="% successful screenings")
    failure_rate: float = Field(ge=0.0, le=100.0, description="% failed screenings")


class DashboardResponse(BaseModel):
    """Complete dashboard analytics."""
    
    success: bool
    
    # Core metrics
    decision_stats: Optional[DecisionStats] = None
    cost_analysis: Optional[CostAnalysis] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    
    # Top insights
    top_missing_skills: List[SkillGapAnalysis] = Field(
        default_factory=list,
        description="Most common skill gaps (top 10)"
    )
    
    # Metadata
    time_range: str = Field(description="Time range for this data")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    error: Optional[str] = None


class SkillGapRequest(BaseModel):
    """Request for skill gap analysis."""
    
    time_range: TimeRange = Field(default=TimeRange.ALL_TIME)
    min_frequency: int = Field(
        default=2,
        ge=1,
        description="Minimum occurrences to include skill"
    )
    decision_filter: Optional[str] = Field(
        default=None,
        description="Filter by decision: HIRE/MAYBE/REJECT"
    )


class SkillGapResponse(BaseModel):
    """Response with skill gap analysis."""
    
    success: bool
    skill_gaps: List[SkillGapAnalysis] = Field(default_factory=list)
    total_candidates_analyzed: int = Field(ge=0)
    time_range: str
    error: Optional[str] = None


class CostRequest(BaseModel):
    """Request for cost analysis."""
    
    time_range: TimeRange = Field(default=TimeRange.ALL_TIME)


class CostResponse(BaseModel):
    """Response with cost analysis."""
    
    success: bool
    cost_analysis: Optional[CostAnalysis] = None
    
    # Historical data points (for charts)
    daily_costs: List[Dict[str, float]] = Field(
        default_factory=list,
        description="Daily cost breakdown: [{'date': '2025-12-26', 'cost': 0.35}]"
    )
    
    error: Optional[str] = None


class ExportFormat(str, Enum):
    """Export file format."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    """Request to export screening results."""
    
    format: ExportFormat = Field(default=ExportFormat.CSV)
    
    # Filters
    time_range: Optional[TimeRange] = Field(default=None)
    decision_filter: Optional[str] = Field(
        default=None,
        description="Filter by decision: HIRE/MAYBE/REJECT"
    )
    min_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Minimum score to include"
    )
    max_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Maximum score to include"
    )
    
    # Options
    include_feedback: bool = Field(
        default=False,
        description="Include full feedback text"
    )
    include_skills: bool = Field(
        default=True,
        description="Include matched/missing skills"
    )


class ExportResponse(BaseModel):
    """Response with export data."""
    
    success: bool
    
    # For direct download
    file_path: Optional[str] = Field(
        default=None,
        description="Path to generated export file"
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Suggested filename"
    )
    
    # For immediate return
    data: Optional[str] = Field(
        default=None,
        description="Export data as string (for CSV/JSON)"
    )
    
    # Metadata
    total_records: int = Field(ge=0, description="Number of records exported")
    format: str = Field(description="Export format used")
    
    error: Optional[str] = None
