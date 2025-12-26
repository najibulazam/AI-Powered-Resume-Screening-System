"""
Job Description Schemas

WHY THIS FILE:
- Defines structured output for Job Analyzer Agent
- Separates "required" vs "nice-to-have" skills
- Captures experience level, seniority, priorities
- Type-safe schema for downstream agents

CONCEPT:
Job descriptions are messy - "5+ years", "Expert in Python", "Team player"
We need structure: Which skills are must-have? What experience level?
This schema converts prose into matchable data.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ExperienceLevel(str, Enum):
    """
    Experience level categorization.
    
    WHY ENUM:
    - Standardizes across different JD phrasings
    - "0-2 years", "Entry level", "Junior" → all map to ENTRY
    - Makes matching logic simpler
    """
    ENTRY = "entry"           # 0-2 years, Junior, Entry-level
    MID = "mid"               # 3-5 years, Mid-level
    SENIOR = "senior"         # 5-8 years, Senior
    LEAD = "lead"             # 8+ years, Lead, Staff, Principal
    EXECUTIVE = "executive"   # Director, VP, C-level


class JobType(str, Enum):
    """Job type categorization"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class WorkLocation(str, Enum):
    """Work location type"""
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


class SkillRequirement(BaseModel):
    """
    Individual skill with importance level.
    
    WHY SEPARATE MODEL:
    - Not all skills are equal
    - "Python (required)" vs "Go (nice to have)"
    - Weighted matching in Phase 6
    """
    skill_name: str = Field(description="Technology, framework, or tool name")
    is_required: bool = Field(description="True if must-have, False if nice-to-have")
    years_experience: Optional[int] = Field(default=None, description="Years of experience needed")
    proficiency_level: Optional[str] = Field(default=None, description="Beginner, Intermediate, Expert")


class Responsibility(BaseModel):
    """Job responsibility/duty"""
    description: str = Field(description="What the person will do")
    is_primary: bool = Field(default=False, description="Is this a core responsibility?")


class JobDescriptionSchema(BaseModel):
    """
    Complete structured job description.
    
    DESIGN PHILOSOPHY:
    - Capture WHAT (skills, responsibilities)
    - Capture WHO (experience level, team size)
    - Capture WHY (company culture, growth)
    - All matchable against ResumeSchema
    
    INTERVIEW POINT:
    "I designed the JD schema to separate signal from noise. Job descriptions
    have fluff ('we're a fast-paced startup!') mixed with requirements.
    My schema extracts the matchable parts - required skills, experience level,
    actual responsibilities - so agents can make data-driven decisions."
    """
    
    # Basic Info
    job_title: str = Field(description="Position title")
    company_name: Optional[str] = Field(default=None, description="Hiring company")
    department: Optional[str] = Field(default=None, description="Engineering, Data Science, etc.")
    job_type: Optional[JobType] = Field(default=None, description="Full-time, contract, etc.")
    work_location: Optional[WorkLocation] = Field(default=None, description="Remote, onsite, hybrid")
    location_city: Optional[str] = Field(default=None, description="City/region if onsite/hybrid")
    
    # Experience Requirements
    experience_level: ExperienceLevel = Field(description="Entry, Mid, Senior, Lead, Executive")
    min_years_experience: Optional[int] = Field(default=None, description="Minimum years required")
    max_years_experience: Optional[int] = Field(default=None, description="Maximum years (if specified)")
    
    # Skills (Most Important for Matching!)
    required_technical_skills: List[SkillRequirement] = Field(
        default_factory=list,
        description="Must-have technical skills"
    )
    preferred_technical_skills: List[SkillRequirement] = Field(
        default_factory=list,
        description="Nice-to-have technical skills"
    )
    required_soft_skills: List[str] = Field(
        default_factory=list,
        description="Must-have soft skills (leadership, communication, etc.)"
    )
    
    # Responsibilities
    responsibilities: List[Responsibility] = Field(
        default_factory=list,
        description="What the person will actually do"
    )
    
    # Education
    required_education_level: Optional[str] = Field(
        default=None,
        description="Bachelor's, Master's, PhD, or None"
    )
    preferred_education_fields: List[str] = Field(
        default_factory=list,
        description="Computer Science, Engineering, etc."
    )
    
    # Company Culture Signals
    company_size: Optional[str] = Field(default=None, description="Startup, Small, Medium, Large, Enterprise")
    team_size: Optional[int] = Field(default=None, description="Size of immediate team")
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Technologies the company uses (for cultural fit)"
    )
    
    # Benefits & Perks (for candidate decision-making)
    salary_range_min: Optional[int] = Field(default=None, description="Minimum salary")
    salary_range_max: Optional[int] = Field(default=None, description="Maximum salary")
    benefits: List[str] = Field(default_factory=list, description="Healthcare, 401k, etc.")
    
    # Additional Context
    industry: Optional[str] = Field(default=None, description="FinTech, HealthTech, E-commerce, etc.")
    growth_opportunities: List[str] = Field(
        default_factory=list,
        description="Career growth, learning, conferences, etc."
    )
    
    @field_validator('required_technical_skills', 'preferred_technical_skills')
    @classmethod
    def clean_skill_requirements(cls, v: List[SkillRequirement]) -> List[SkillRequirement]:
        """
        Remove duplicates and standardize skill names.
        
        WHY:
        - LLMs might extract "Python" and "python" as separate
        - Duplicates waste matching time
        """
        if not v:
            return []
        
        # Deduplicate by lowercase skill name
        seen = set()
        cleaned = []
        for skill in v:
            key = skill.skill_name.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(skill)
        
        return cleaned
    
    @field_validator('job_title')
    @classmethod
    def validate_job_title(cls, v: str) -> str:
        """Ensure job title is not empty"""
        if not v or not v.strip():
            raise ValueError("Job title cannot be empty")
        return v.strip()


class JobAnalyzeRequest(BaseModel):
    """Request to analyze job description text"""
    text: str = Field(description="Clean job description text")


class JobAnalyzeResponse(BaseModel):
    """
    Response from Job Analyzer Agent.
    
    WHY WRAPPER:
    - Consistent API pattern (same as ResumeParseResponse)
    - Success/error handling
    - Metadata (processing time, confidence)
    """
    success: bool = Field(description="Whether analysis succeeded")
    job_data: Optional[JobDescriptionSchema] = Field(default=None, description="Extracted job data")
    error_message: Optional[str] = Field(default=None, description="Error if failed")
    confidence_score: Optional[float] = Field(
        default=None,
        description="0.0-1.0 confidence in extraction quality"
    )
    processing_time_ms: Optional[int] = Field(default=None, description="Time taken in milliseconds")
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Confidence must be between 0 and 1"""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


# ===========================================
# EDUCATIONAL COMPARISON
# ===========================================

"""
DESIGN PATTERN: Parallel Schemas

Notice how JobDescriptionSchema mirrors ResumeSchema:

RESUME SIDE:                    JOB SIDE:
- technical_skills: List        - required_technical_skills: List
- work_experience: List         - responsibilities: List
- total_years_experience        - min_years_experience

WHY PARALLEL:
When Phase 6 (Skill Matcher) compares them, it's apple-to-apple:
- Resume skills → Job required_skills
- Resume experience → Job min_years_experience
- Resume responsibilities → Job responsibilities

This is deliberate schema design for downstream matching.

INTERVIEW POINT:
"I designed the resume and job schemas to be parallel - same structure,
different perspectives. This makes the matching agent (Phase 6) much
simpler because it's comparing equivalent data types. It's the same
principle as database normalization - structured data flows cleanly
through the pipeline."
"""
