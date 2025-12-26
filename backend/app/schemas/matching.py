"""
Matching Schemas

WHY THIS FILE:
- Defines output structure for Skill Matcher Agent
- Captures match results, skill gaps, recommendations
- Structured data for scoring and feedback agents

CONCEPT:
Matching is the bridge between Resume and Job Description.
Input: What candidate HAS + What company NEEDS
Output: How well they align + What's missing + Recommendations

DESIGN PHILOSOPHY:
- Quantitative: Match percentages (objective)
- Qualitative: Skill gaps (actionable)
- Recommendations: What to learn (helpful)
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MatchLevel(str, Enum):
    """
    Overall match quality categorization.
    
    WHY ENUM:
    - Easy filtering (show only STRONG matches)
    - Clear interpretation for users
    - Consistent across system
    """
    EXCELLENT = "excellent"  # 90-100% match
    STRONG = "strong"        # 75-89% match
    GOOD = "good"            # 60-74% match
    FAIR = "fair"            # 40-59% match
    WEAK = "weak"            # 0-39% match


class SkillMatch(BaseModel):
    """
    Individual skill match result.
    
    WHY TRACK EACH SKILL:
    - Transparency: Show which skills matched
    - Feedback: Explain why candidate is strong/weak
    - Debugging: Verify matching logic
    """
    skill_name: str = Field(description="Skill being matched")
    is_match: bool = Field(description="True if candidate has this skill")
    is_required: bool = Field(description="True if job requires it (vs preferred)")
    candidate_has: bool = Field(description="Candidate possesses this skill")
    job_needs: bool = Field(default=True, description="Job needs this skill")
    years_required: Optional[int] = Field(default=None, description="Years of experience required")
    years_candidate_has: Optional[float] = Field(default=None, description="Years candidate has")


class SkillGap(BaseModel):
    """
    Missing skill that candidate should learn.
    
    WHY SEPARATE MODEL:
    - Actionable feedback ("You need to learn X")
    - Prioritization (required skills first)
    - Learning recommendations
    """
    skill_name: str = Field(description="Missing skill")
    is_required: bool = Field(description="Is this a required skill (deal-breaker)?")
    priority: str = Field(description="HIGH, MEDIUM, LOW based on job requirements")
    reason: str = Field(description="Why this skill matters for the role")
    learning_resources: List[str] = Field(
        default_factory=list,
        description="Suggested courses/tutorials (can be added in feedback phase)"
    )


class ExperienceMatch(BaseModel):
    """
    How candidate's experience aligns with job requirements.
    
    WHY SEPARATE:
    - Experience is different from skills
    - Numeric comparison (years)
    - Context matters (7 years vs 5 required is great, 2 years vs 5 is not)
    """
    candidate_total_years: float = Field(description="Candidate's total experience")
    job_min_years: Optional[int] = Field(description="Job minimum years required")
    job_max_years: Optional[int] = Field(default=None, description="Job maximum years (if specified)")
    is_sufficient: bool = Field(description="Does candidate meet minimum?")
    is_overqualified: bool = Field(default=False, description="Too much experience?")
    experience_level_match: bool = Field(
        description="Does candidate level match job level (entry/mid/senior)?"
    )


class EducationMatch(BaseModel):
    """
    Education requirements match.
    
    SIMPLE FOR NOW:
    - Just checking if candidate meets minimum
    - Can be expanded later (field of study match, GPA, etc.)
    """
    candidate_highest_degree: Optional[str] = Field(default=None, description="Bachelor's, Master's, PhD")
    job_required_degree: Optional[str] = Field(default=None, description="Required education level")
    meets_requirement: bool = Field(description="Does candidate meet minimum?")
    field_matches: bool = Field(default=True, description="Does field of study align?")


class MatchResult(BaseModel):
    """
    Complete matching result between resume and job.
    
    THIS IS THE CORE OUTPUT OF PHASE 6.
    
    STRUCTURE:
    1. Overall scores (high-level view)
    2. Skill breakdown (detailed analysis)
    3. Experience & education (additional factors)
    4. Recommendations (actionable next steps)
    
    INTERVIEW POINT:
    "The MatchResult schema is designed for multiple consumers:
    - Scoring Agent (Phase 7) uses overall_score for decisions
    - Feedback Agent (Phase 8) uses skill_gaps for recommendations
    - UI displays skill_matches for transparency
    Each agent gets what it needs without re-computation."
    """
    
    # ============================================
    # OVERALL SCORES
    # ============================================
    
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall match score (0-100)"
    )
    match_level: MatchLevel = Field(description="Qualitative match level")
    
    # Skill matching scores
    required_skills_match_percent: float = Field(
        ge=0.0,
        le=100.0,
        description="% of required skills candidate has"
    )
    preferred_skills_match_percent: float = Field(
        ge=0.0,
        le=100.0,
        description="% of preferred skills candidate has"
    )
    
    # ============================================
    # DETAILED BREAKDOWNS
    # ============================================
    
    # Skills
    matched_required_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Required skills that candidate HAS"
    )
    missing_required_skills: List[SkillGap] = Field(
        default_factory=list,
        description="Required skills candidate is MISSING (deal-breakers)"
    )
    matched_preferred_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Preferred skills candidate HAS (bonus points)"
    )
    missing_preferred_skills: List[SkillGap] = Field(
        default_factory=list,
        description="Preferred skills candidate is MISSING"
    )
    
    # Experience & Education
    experience_match: ExperienceMatch = Field(description="Experience fit analysis")
    education_match: EducationMatch = Field(description="Education requirements check")
    
    # ============================================
    # INSIGHTS & RECOMMENDATIONS
    # ============================================
    
    key_strengths: List[str] = Field(
        default_factory=list,
        description="What makes this candidate strong (for feedback)"
    )
    key_weaknesses: List[str] = Field(
        default_factory=list,
        description="What this candidate is missing (for feedback)"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggested actions for candidate"
    )
    
    # ============================================
    # METADATA
    # ============================================
    
    resume_id: Optional[str] = Field(default=None, description="Resume identifier")
    job_id: Optional[str] = Field(default=None, description="Job identifier")
    timestamp: Optional[str] = Field(default=None, description="When matching was performed")
    
    @field_validator('overall_score', 'required_skills_match_percent', 'preferred_skills_match_percent')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure percentages are between 0-100"""
        if v < 0 or v > 100:
            raise ValueError("Score must be between 0 and 100")
        return round(v, 2)


class MatchRequest(BaseModel):
    """
    Request to match resume against job.
    
    OPTIONS:
    1. Provide parsed data directly (resume_data + job_data)
    2. Provide file IDs (resume_file_id + job_file_id) - endpoint will parse
    
    Option 1 is for when you already have parsed data.
    Option 2 is end-to-end convenience.
    """
    resume_file_id: Optional[str] = Field(default=None, description="Resume file ID")
    job_file_id: Optional[str] = Field(default=None, description="Job description file ID")
    
    # Or provide data directly
    resume_data: Optional[dict] = Field(default=None, description="Parsed resume data")
    job_data: Optional[dict] = Field(default=None, description="Parsed job data")


class MatchResponse(BaseModel):
    """
    Response from Skill Matcher Agent.
    
    CONSISTENCY:
    Same pattern as ResumeParseResponse and JobAnalyzeResponse:
    - success flag
    - error handling
    - metadata (processing time)
    """
    success: bool = Field(description="Whether matching succeeded")
    match_result: Optional[MatchResult] = Field(default=None, description="Match results")
    error_message: Optional[str] = Field(default=None, description="Error if failed")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")


# ===========================================
# EDUCATIONAL COMPARISON
# ===========================================

"""
DESIGN PATTERN: Result Schema vs Process Schema

PROCESS SCHEMAS (Input):
- ResumeSchema: What candidate has
- JobDescriptionSchema: What job needs

RESULT SCHEMA (Output):
- MatchResult: How well they align

WHY SEPARATE:
- Separation of concerns (data vs analysis)
- Different consumers (Resume Parser creates ResumeSchema, Skill Matcher creates MatchResult)
- Reusability (same MatchResult structure even if matching logic changes)

PIPELINE:
Phase 4 → ResumeSchema
Phase 5 → JobDescriptionSchema
Phase 6 → MatchResult (combines the two)
Phase 7 → Uses MatchResult.overall_score for decision
Phase 8 → Uses MatchResult.skill_gaps for feedback

Each phase produces output that next phase consumes.
This is CLEAN ARCHITECTURE.

INTERVIEW POINT:
"I designed the schemas to separate data (what exists) from analysis (what we learned).
ResumeSchema and JobDescriptionSchema are facts - they describe reality.
MatchResult is insight - it tells us something NEW by comparing the facts.
This separation makes the system flexible - I can change the matching algorithm
without touching the data schemas, and vice versa."
"""
