"""
File Upload Schemas

WHY THESE SCHEMAS EXIST:
- Define what data clients send/receive
- Validate file metadata before saving
- Document API contracts for frontend developers

AGENTIC CONNECTION:
These schemas are the "input layer" before agents process data.
Think: User → Upload Schema → Saved File → Agent Input Schema
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class JobDescriptionUploadResponse(BaseModel):
    """
    Response after successfully uploading a job description.
    
    WHY: Frontend needs the file_id to reference this JD later
    when triggering the screening process.
    """
    file_id: str = Field(..., description="Unique identifier for the uploaded job description")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    message: str = "Job description uploaded successfully"


class ResumeUploadResponse(BaseModel):
    """
    Response after uploading resumes (potentially multiple files).
    
    WHY: Users can upload 1-100 resumes at once.
    We need to track each file separately for the agent pipeline.
    """
    file_ids: List[str] = Field(..., description="List of unique identifiers for uploaded resumes")
    filenames: List[str] = Field(..., description="Original filenames")
    total_files: int = Field(..., description="Number of successfully uploaded files")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    message: str = "Resumes uploaded successfully"


class FileMetadata(BaseModel):
    """
    Internal model for tracking file information.
    
    WHY: Before agents process files, we need metadata:
    - Where is the file stored?
    - What type is it (JD vs Resume)?
    - When was it uploaded?
    
    This helps with debugging and auditing.
    """
    file_id: str
    filename: str
    file_path: str  # Actual path on disk
    file_type: str  # "job_description" or "resume"
    file_size: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "jd_20231226_abc123",
                "filename": "senior_developer.pdf",
                "file_path": "uploads/job_descriptions/jd_20231226_abc123.pdf",
                "file_type": "job_description",
                "file_size": 45678,
                "uploaded_at": "2023-12-26T10:30:00"
            }
        }


class UploadErrorResponse(BaseModel):
    """
    Standardized error response for upload failures.
    
    WHY: Consistent error format helps frontend handle failures gracefully.
    """
    error: str
    detail: Optional[str] = None
    file_name: Optional[str] = None
