"""
Database Models for PostgreSQL

Defines SQLAlchemy models for persistent storage of screening results.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ARRAY, DateTime, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class ScreeningResultModel(Base):
    """
    SQLAlchemy model for screening results.
    
    Maps to screening_results table created by init.sql.
    """
    __tablename__ = "screening_results"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Info
    candidate_name = Column(String(255), nullable=False, index=True)
    job_title = Column(String(255), nullable=False, index=True)
    
    # Decision
    decision = Column(String(20), nullable=False, index=True)  # HIRE, MAYBE, REJECT
    overall_score = Column(DECIMAL(5, 2), nullable=False, index=True)
    
    # Skills (PostgreSQL arrays)
    matched_skills = Column(ARRAY(Text), default=list)
    missing_skills = Column(ARRAY(Text), default=list)
    
    # Review Metadata
    human_review_required = Column(Boolean, default=False, index=True)
    review_priority = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Cost & Performance
    cost_usd = Column(DECIMAL(10, 6), nullable=False, default=0)
    processing_time_ms = Column(Integer, nullable=False)
    
    # Optional Feedback
    feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScreeningResult(id={self.id}, candidate={self.candidate_name}, decision={self.decision}, score={self.overall_score})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "decision": self.decision,
            "overall_score": float(self.overall_score),
            "matched_skills": self.matched_skills or [],
            "missing_skills": self.missing_skills or [],
            "human_review_required": self.human_review_required,
            "review_priority": self.review_priority,
            "cost_usd": float(self.cost_usd),
            "processing_time_ms": self.processing_time_ms,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
