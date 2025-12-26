"""
Database Service

Handles database connections and operations for screening results.
Falls back to in-memory storage if database is not configured.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.models.database import Base, ScreeningResultModel
from app.schemas.orchestration import ScreeningResult
from app.config import settings
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for managing screening results in PostgreSQL.
    
    Falls back to in-memory storage if DATABASE_URL is not configured.
    """
    
    def __init__(self):
        self.use_db = settings.use_database
        self.engine = None
        self.SessionLocal = None
        self.in_memory_results: List[ScreeningResult] = []
        
        if self.use_db:
            try:
                self._init_database()
                logger.info("✓ Database connected successfully")
            except Exception as e:
                logger.warning(f"Database connection failed: {e}. Using in-memory storage.")
                self.use_db = False
        else:
            logger.info("No DATABASE_URL configured. Using in-memory storage.")
    
    def _init_database(self):
        """Initialize database connection and create tables."""
        self.engine = create_engine(
            settings.database_url,
            poolclass=NullPool,
            echo=settings.debug
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session."""
        if not self.use_db or not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    async def add_result(self, result: ScreeningResult):
        """Add screening result to storage."""
        if self.use_db:
            self._add_to_database(result)
        else:
            self.in_memory_results.append(result)
    
    def _add_to_database(self, result: ScreeningResult):
        """Add result to PostgreSQL."""
        session = self.get_session()
        try:
            model = ScreeningResultModel(
                candidate_name=result.candidate_name,
                job_title=result.job_title,
                decision=result.decision,
                overall_score=result.overall_score,
                matched_skills=result.matched_skills,
                missing_skills=result.missing_skills,
                human_review_required=result.human_review_required,
                review_priority=result.review_priority,
                cost_usd=result.cost_usd,
                processing_time_ms=result.processing_time_ms,
                feedback=result.feedback
            )
            session.add(model)
            session.commit()
            logger.debug(f"Added result to database: {result.candidate_name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add result to database: {e}")
            raise
        finally:
            session.close()
    
    def get_all_results(self, 
                       time_range: Optional[str] = None,
                       decision_filter: Optional[str] = None,
                       min_score: Optional[float] = None,
                       max_score: Optional[float] = None) -> List[ScreeningResult]:
        """Get all screening results with optional filters."""
        if self.use_db:
            return self._get_from_database(time_range, decision_filter, min_score, max_score)
        else:
            return self._get_from_memory(time_range, decision_filter, min_score, max_score)
    
    def _get_from_database(self,
                          time_range: Optional[str],
                          decision_filter: Optional[str],
                          min_score: Optional[float],
                          max_score: Optional[float]) -> List[ScreeningResult]:
        """Get results from PostgreSQL."""
        session = self.get_session()
        try:
            query = session.query(ScreeningResultModel)
            
            # Time range filter
            if time_range:
                cutoff = self._get_time_cutoff(time_range)
                if cutoff:
                    query = query.filter(ScreeningResultModel.created_at >= cutoff)
            
            # Decision filter
            if decision_filter:
                query = query.filter(ScreeningResultModel.decision == decision_filter.upper())
            
            # Score filters
            if min_score is not None:
                query = query.filter(ScreeningResultModel.overall_score >= min_score)
            if max_score is not None:
                query = query.filter(ScreeningResultModel.overall_score <= max_score)
            
            # Order by newest first
            query = query.order_by(desc(ScreeningResultModel.created_at))
            
            models = query.all()
            
            # Convert to ScreeningResult objects
            results = []
            for model in models:
                results.append(ScreeningResult(
                    candidate_name=model.candidate_name,
                    job_title=model.job_title,
                    decision=model.decision,
                    overall_score=float(model.overall_score),
                    matched_skills=model.matched_skills or [],
                    missing_skills=model.missing_skills or [],
                    human_review_required=model.human_review_required,
                    review_priority=model.review_priority,
                    cost_usd=float(model.cost_usd),
                    processing_time_ms=model.processing_time_ms,
                    feedback=model.feedback
                ))
            
            return results
        finally:
            session.close()
    
    def _get_from_memory(self,
                        time_range: Optional[str],
                        decision_filter: Optional[str],
                        min_score: Optional[float],
                        max_score: Optional[float]) -> List[ScreeningResult]:
        """Get results from in-memory storage."""
        results = self.in_memory_results.copy()
        
        # Decision filter
        if decision_filter:
            results = [r for r in results if r.decision.upper() == decision_filter.upper()]
        
        # Score filters
        if min_score is not None:
            results = [r for r in results if r.overall_score >= min_score]
        if max_score is not None:
            results = [r for r in results if r.overall_score <= max_score]
        
        # Note: Time range filtering not implemented for in-memory
        # (requires storing timestamps which ScreeningResult doesn't have)
        
        return results
    
    def _get_time_cutoff(self, time_range: str) -> Optional[datetime]:
        """Calculate time cutoff for filtering."""
        now = datetime.utcnow()
        
        if time_range == "TODAY":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "WEEK":
            return now - timedelta(days=7)
        elif time_range == "MONTH":
            return now - timedelta(days=30)
        elif time_range == "QUARTER":
            return now - timedelta(days=90)
        elif time_range == "YEAR":
            return now - timedelta(days=365)
        else:  # ALL_TIME
            return None
    
    def get_count(self) -> int:
        """Get total number of results."""
        if self.use_db:
            session = self.get_session()
            try:
                return session.query(ScreeningResultModel).count()
            finally:
                session.close()
        else:
            return len(self.in_memory_results)
    
    def clear_results(self):
        """Clear all results (for testing only)."""
        if self.use_db:
            session = self.get_session()
            try:
                session.query(ScreeningResultModel).delete()
                session.commit()
                logger.info("Cleared all results from database")
            finally:
                session.close()
        else:
            self.in_memory_results.clear()
            logger.info("Cleared all results from memory")


# Global database service instance
db_service = DatabaseService()
