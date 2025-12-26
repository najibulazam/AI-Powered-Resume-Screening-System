"""
Parsing Response Schemas

WHY: API endpoints need to return parsing results before agent processing.
These schemas show what was extracted from files.
"""

from pydantic import BaseModel, Field
from typing import List


class ParsedDocumentResponse(BaseModel):
    """
    Response after parsing a single document.
    
    WHY: Frontend needs to show users what was extracted
    before triggering expensive agent processing.
    """
    file_id: str = Field(..., description="Original file ID from upload")
    filename: str
    text_preview: str = Field(..., description="First 500 chars of cleaned text")
    page_count: int
    char_count: int
    word_count: int
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "resume_20231226_abc123",
                "filename": "john_doe_resume.pdf",
                "text_preview": "JOHN DOE\nSenior Software Engineer...",
                "page_count": 2,
                "char_count": 3420,
                "word_count": 580,
                "is_valid": True,
                "validation_errors": []
            }
        }


class BatchParseResponse(BaseModel):
    """
    Response after parsing multiple documents (e.g., all uploaded resumes).
    """
    total_files: int
    parsed_successfully: int
    parsing_errors: int
    documents: List[ParsedDocumentResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 3,
                "parsed_successfully": 2,
                "parsing_errors": 1,
                "documents": [
                    {
                        "file_id": "resume_001",
                        "filename": "candidate1.pdf",
                        "text_preview": "...",
                        "is_valid": True,
                        "validation_errors": []
                    }
                ]
            }
        }
