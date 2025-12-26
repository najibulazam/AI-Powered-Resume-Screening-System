"""
Resume Data Schema

WHY THIS FILE:
Defines the exact structure of data extracted from resumes.
This is the "contract" between Resume Parser Agent and downstream agents.

AGENTIC PRINCIPLE:
Schemas create clear boundaries. The parser agent MUST return this structure,
and the skill matcher agent EXPECTS this structure. Type safety prevents bugs.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class Education(BaseModel):
    """
    Educational background entry.
    
    WHY NESTED MODEL:
    - Resumes have multiple education entries
    - Each has its own fields (degree, school, dates)
    - Easier to validate individually
    """
    degree: str = Field(..., description="Degree name (e.g., Bachelor of Science)")
    field_of_study: Optional[str] = Field(None, description="Major/specialization")
    institution: str = Field(..., description="School/university name")
    graduation_year: Optional[int] = Field(None, description="Year graduated", ge=1950, le=2030)
    gpa: Optional[float] = Field(None, description="GPA if mentioned", ge=0.0, le=4.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "degree": "Bachelor of Science in Computer Science",
                "field_of_study": "Computer Science",
                "institution": "University of Technology",
                "graduation_year": 2016,
                "gpa": 3.7
            }
        }


class WorkExperience(BaseModel):
    """
    Work experience entry.
    
    WHY STRUCTURED:
    - Need to calculate total years experience
    - Match job titles to requirements
    - Track skill progression over time
    """
    job_title: Optional[str] = Field(None, description="Position/role title")
    company: Optional[str] = Field(None, description="Company name")
    start_date: Optional[str] = Field(None, description="Start date (any format)")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    duration_months: Optional[int] = Field(None, description="Calculated duration", ge=0)
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    technologies_used: List[str] = Field(default_factory=list, description="Tech stack mentioned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Software Engineer",
                "company": "Tech Innovations Inc.",
                "start_date": "2021",
                "end_date": "Present",
                "duration_months": 48,
                "responsibilities": [
                    "Built ML pipeline processing 10M+ documents",
                    "Led team of 3 engineers"
                ],
                "technologies_used": ["Python", "FastAPI", "Docker"]
            }
        }


class ResumeSchema(BaseModel):
    """
    Complete structured resume data.
    
    WHY THIS SCHEMA:
    - Resume Parser Agent outputs this
    - Skill Matcher Agent inputs this
    - Scorer Agent uses this
    - Type-safe throughout pipeline
    
    DESIGN DECISIONS:
    - Optional fields: Not all resumes have everything
    - Lists for multiple entries: Skills, jobs, education
    - Validators: Ensure data quality
    """
    
    # Personal Information
    full_name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City, State or Country")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio_url: Optional[str] = Field(None, description="Personal website/portfolio")
    
    # Professional Summary
    summary: Optional[str] = Field(None, description="Professional summary or objective")
    
    # Skills
    technical_skills: List[str] = Field(
        default_factory=list,
        description="Programming languages, frameworks, tools"
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Communication, leadership, etc."
    )
    
    # Experience
    work_experience: List[WorkExperience] = Field(
        default_factory=list,
        description="Work history in reverse chronological order"
    )
    total_years_experience: Optional[float] = Field(
        None,
        description="Total years of professional experience",
        ge=0,
        le=50
    )
    
    # Education
    education: List[Education] = Field(
        default_factory=list,
        description="Educational background"
    )
    
    # Additional
    certifications: List[str] = Field(
        default_factory=list,
        description="Professional certifications"
    )
    languages: List[str] = Field(
        default_factory=list,
        description="Spoken/written languages"
    )
    projects: List[str] = Field(
        default_factory=list,
        description="Notable projects or achievements"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """
        Basic email validation.
        
        WHY: LLMs sometimes extract malformed emails.
        Better to catch here than pass bad data downstream.
        """
        if v and '@' not in v:
            return None  # Invalid, return None instead of failing
        return v
    
    @field_validator('technical_skills', 'soft_skills')
    @classmethod
    def remove_empty_skills(cls, v: List[str]) -> List[str]:
        """
        Remove empty strings from skill lists.
        
        WHY: LLMs sometimes return ["Python", "", "Java"]
        Clean it up here to avoid issues later.
        """
        return [skill.strip() for skill in v if skill and skill.strip()]
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "(555) 123-4567",
                "location": "San Francisco, CA",
                "linkedin_url": "linkedin.com/in/johndoe",
                "github_url": "github.com/johndoe",
                "summary": "Senior Software Engineer with 7+ years experience...",
                "technical_skills": [
                    "Python", "FastAPI", "Docker", "AWS", "PostgreSQL"
                ],
                "soft_skills": [
                    "Leadership", "Communication", "Problem Solving"
                ],
                "work_experience": [
                    {
                        "job_title": "Senior ML Engineer",
                        "company": "Tech Innovations Inc.",
                        "start_date": "2021",
                        "end_date": "Present",
                        "duration_months": 48,
                        "responsibilities": ["Built ML pipeline"],
                        "technologies_used": ["Python", "FastAPI"]
                    }
                ],
                "total_years_experience": 7.0,
                "education": [
                    {
                        "degree": "Bachelor of Science",
                        "field_of_study": "Computer Science",
                        "institution": "University of Technology",
                        "graduation_year": 2016,
                        "gpa": 3.7
                    }
                ],
                "certifications": ["AWS Certified Solutions Architect"],
                "languages": ["English", "Spanish"],
                "projects": ["Open source contributor to FastAPI"]
            }
        }


class ResumeParseRequest(BaseModel):
    """
    Request to parse a resume.
    
    WHY SEPARATE REQUEST SCHEMA:
    - API endpoint validation
    - Clear what clients need to send
    - Can add options (e.g., strict_mode, language)
    """
    text: str = Field(..., description="Clean resume text to parse", min_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "John Doe\nSenior Software Engineer\nEmail: john@example.com..."
            }
        }


class ResumeParseResponse(BaseModel):
    """
    Response from resume parsing.
    
    WHY WRAPPER:
    - Include metadata (confidence, processing time)
    - Consistent API response format
    - Can add warnings/errors without breaking schema
    """
    success: bool
    resume_data: Optional[ResumeSchema] = None
    error_message: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "resume_data": {
                    "full_name": "John Doe",
                    "technical_skills": ["Python", "FastAPI"],
                    "total_years_experience": 7.0
                },
                "error_message": None,
                "confidence_score": 0.95,
                "processing_time_ms": 1250
            }
        }
