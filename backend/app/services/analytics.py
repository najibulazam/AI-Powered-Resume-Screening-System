"""
Analytics service for screening data analysis.

This service computes aggregate statistics, identifies trends,
and generates insights from screening results.

Now uses DatabaseService for persistent storage with fallback to in-memory.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter
import statistics

from app.schemas.orchestration import ScreeningResult
from app.schemas.analytics import (
    DecisionStats, SkillGapAnalysis, CostAnalysis,
    PerformanceMetrics, TimeRange
)
from app.services.database import db_service

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Compute analytics and insights from screening results.
    
    Uses DatabaseService which automatically handles:
    - PostgreSQL storage (if DATABASE_URL configured)
    - In-memory storage (fallback for development)
    
    Responsibilities:
    - Aggregate statistics (decisions, scores, costs)
    - Skill gap analysis (most common missing skills)
    - Performance metrics (timing, success rates)
    - Trend analysis (over time)
    """
    
    def __init__(self):
        """Initialize analytics service with database backend."""
        self.db = db_service
        logger.info(f"Analytics service initialized (using {'database' if self.db.use_db else 'in-memory'} storage)")
    
    async def add_result(self, result: ScreeningResult):
        """Add a screening result to analytics storage."""
        await self.db.add_result(result)
    
    def clear_results(self):
        """Clear all stored results (for testing only)."""
        self.db.clear_results()
    
    def get_decision_stats(
        self,
        time_range: Optional[TimeRange] = None
    ) -> DecisionStats:
        """
        Compute decision statistics.
        
        Args:
            time_range: Filter by time range
            
        Returns:
            DecisionStats with aggregated metrics
        """
        results = self._filter_by_time(time_range)
        
        if not results:
            return DecisionStats(
                total_candidates=0,
                hire_count=0,
                maybe_count=0,
                reject_count=0,
                hire_percent=0.0,
                maybe_percent=0.0,
                reject_percent=0.0,
                avg_score=0.0,
                median_score=0.0,
                human_review_required=0,
                human_review_percent=0.0
            )
        
        total = len(results)
        
        # Count decisions
        hire_count = sum(1 for r in results if r.decision.upper() == "HIRE")
        maybe_count = sum(1 for r in results if r.decision.upper() == "MAYBE")
        reject_count = sum(1 for r in results if r.decision.upper() == "REJECT")
        
        # Scores
        scores = [r.overall_score for r in results]
        avg_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        
        # Human review
        human_review = sum(1 for r in results if r.requires_human_review)
        
        return DecisionStats(
            total_candidates=total,
            hire_count=hire_count,
            maybe_count=maybe_count,
            reject_count=reject_count,
            hire_percent=(hire_count / total * 100) if total > 0 else 0.0,
            maybe_percent=(maybe_count / total * 100) if total > 0 else 0.0,
            reject_percent=(reject_count / total * 100) if total > 0 else 0.0,
            avg_score=avg_score,
            median_score=median_score,
            human_review_required=human_review,
            human_review_percent=(human_review / total * 100) if total > 0 else 0.0
        )
    
    def get_skill_gap_analysis(
        self,
        time_range: Optional[TimeRange] = None,
        min_frequency: int = 2,
        decision_filter: Optional[str] = None
    ) -> List[SkillGapAnalysis]:
        """
        Analyze most common missing skills.
        
        Args:
            time_range: Filter by time range
            min_frequency: Minimum occurrences to include
            decision_filter: Filter by decision (HIRE/MAYBE/REJECT)
            
        Returns:
            List of SkillGapAnalysis sorted by frequency
        """
        results = self._filter_by_time(time_range)
        
        # Apply decision filter
        if decision_filter:
            results = [
                r for r in results
                if r.decision.upper() == decision_filter.upper()
            ]
        
        if not results:
            return []
        
        total_candidates = len(results)
        
        # Count missing skills across all candidates
        skill_gaps = Counter()
        for result in results:
            for skill in result.missing_skills:
                skill_gaps[skill] += 1
        
        # Filter by minimum frequency
        skill_gaps_filtered = Counter({
            skill: count
            for skill, count in skill_gaps.items()
            if count >= min_frequency
        })
        
        # Analyze skill context (HIRE vs REJECT)
        hire_results = [r for r in results if r.decision.upper() == "HIRE"]
        reject_results = [r for r in results if r.decision.upper() == "REJECT"]
        
        analyses = []
        for skill, count in skill_gaps_filtered.most_common(20):  # Top 20
            gap_percent = (count / total_candidates * 100)
            
            # Determine priority based on frequency
            if gap_percent >= 50:
                priority = "HIGH"
            elif gap_percent >= 25:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            # Check if this skill appears in HIRE vs REJECT patterns
            hire_missing = sum(
                1 for r in hire_results
                if skill in r.missing_skills
            )
            reject_missing = sum(
                1 for r in reject_results
                if skill in r.missing_skills
            )
            
            typical_in_hires = False
            typical_in_rejects = False
            
            if len(hire_results) > 0:
                typical_in_hires = (hire_missing / len(hire_results)) < 0.2
            
            if len(reject_results) > 0:
                typical_in_rejects = (reject_missing / len(reject_results)) > 0.6
            
            analyses.append(
                SkillGapAnalysis(
                    skill_name=skill,
                    gap_frequency=count,
                    gap_percent=gap_percent,
                    priority=priority,
                    typical_in_hires=typical_in_hires,
                    typical_in_rejects=typical_in_rejects
                )
            )
        
        return analyses
    
    def get_cost_analysis(
        self,
        time_range: Optional[TimeRange] = None
    ) -> CostAnalysis:
        """
        Analyze costs and spending.
        
        Args:
            time_range: Filter by time range
            
        Returns:
            CostAnalysis with spending breakdown
        """
        results = self._filter_by_time(time_range)
        
        if not results:
            return CostAnalysis(
                total_cost_usd=0.0,
                cost_per_candidate=0.0,
                resume_parsing_cost=0.0,
                job_parsing_cost=0.0,
                feedback_cost=0.0,
                estimated_monthly_cost=0.0,
                estimated_annual_cost=0.0
            )
        
        total_cost = sum(r.cost_usd for r in results)
        cost_per_candidate = total_cost / len(results) if results else 0.0
        
        # Phase breakdown (based on typical costs)
        # Resume: $0.002, Job: $0.002, Feedback: $0.003
        num_candidates = len(results)
        resume_cost = num_candidates * 0.002
        job_cost = num_candidates * 0.002  # Note: Can be amortized in batches
        feedback_cost = num_candidates * 0.003
        
        # Projections (assuming current rate continues)
        # Calculate daily rate from time range
        if time_range == TimeRange.TODAY:
            daily_cost = total_cost
        elif time_range == TimeRange.WEEK:
            daily_cost = total_cost / 7
        elif time_range == TimeRange.MONTH:
            daily_cost = total_cost / 30
        else:
            # Estimate based on results
            daily_cost = cost_per_candidate * 10  # Assume 10 candidates/day
        
        monthly_cost = daily_cost * 30
        annual_cost = daily_cost * 365
        
        return CostAnalysis(
            total_cost_usd=total_cost,
            cost_per_candidate=cost_per_candidate,
            resume_parsing_cost=resume_cost,
            job_parsing_cost=job_cost,
            feedback_cost=feedback_cost,
            estimated_monthly_cost=monthly_cost,
            estimated_annual_cost=annual_cost
        )
    
    def get_performance_metrics(
        self,
        time_range: Optional[TimeRange] = None
    ) -> PerformanceMetrics:
        """
        Compute performance and timing metrics.
        
        Args:
            time_range: Filter by time range
            
        Returns:
            PerformanceMetrics with timing statistics
        """
        results = self._filter_by_time(time_range)
        
        if not results:
            return PerformanceMetrics(
                total_screenings=0,
                avg_processing_time_ms=0.0,
                median_processing_time_ms=0.0,
                min_processing_time_ms=0.0,
                max_processing_time_ms=0.0,
                avg_parsing_time_ms=0.0,
                avg_extraction_time_ms=0.0,
                avg_matching_time_ms=0.0,
                avg_scoring_time_ms=0.0,
                avg_feedback_time_ms=0.0,
                success_rate=0.0,
                failure_rate=0.0
            )
        
        # Processing times
        times = [r.processing_time_ms for r in results]
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        # Phase breakdown (estimated)
        # Total ~5000ms: Parsing ~0ms, Extraction ~3000ms, Matching ~10ms, Scoring ~1ms, Feedback ~2000ms
        avg_parsing = 0  # Negligible
        avg_extraction = avg_time * 0.6  # 60% of time
        avg_matching = 10  # Fixed
        avg_scoring = 1  # Fixed
        avg_feedback = avg_time * 0.4  # 40% of time
        
        # Success rate (all results here are successful)
        # In production, would track failures from database
        success_rate = 100.0
        failure_rate = 0.0
        
        return PerformanceMetrics(
            total_screenings=len(results),
            avg_processing_time_ms=avg_time,
            median_processing_time_ms=median_time,
            min_processing_time_ms=min_time,
            max_processing_time_ms=max_time,
            avg_parsing_time_ms=avg_parsing,
            avg_extraction_time_ms=avg_extraction,
            avg_matching_time_ms=avg_matching,
            avg_scoring_time_ms=avg_scoring,
            avg_feedback_time_ms=avg_feedback,
            success_rate=success_rate,
            failure_rate=failure_rate
        )
    
    def export_to_csv(
        self,
        results: Optional[List[ScreeningResult]] = None,
        include_feedback: bool = False,
        include_skills: bool = True
    ) -> str:
        """
        Export results to CSV format.
        
        Args:
            results: Results to export (uses all if None)
            include_feedback: Include full feedback text
            include_skills: Include matched/missing skills
            
        Returns:
            CSV string
        """
        if results is None:
            results = self.db.get_all_results()
        
        if not results:
            return "No results to export"
        
        # CSV header
        headers = [
            "Candidate Name",
            "Decision",
            "Score",
            "Confidence",
            "Human Review Required",
            "Review Priority",
            "Processing Time (ms)",
            "Cost (USD)"
        ]
        
        if include_skills:
            headers.extend([
                "Matched Skills",
                "Missing Skills",
                "Strengths",
                "Weaknesses"
            ])
        
        if include_feedback:
            headers.append("Feedback")
        
        csv_lines = [",".join(headers)]
        
        # Data rows
        for result in results:
            row = [
                f'"{result.candidate_name}"',
                result.decision,
                str(result.overall_score),
                result.confidence,
                str(result.requires_human_review),
                result.review_priority,
                str(result.processing_time_ms),
                str(result.cost_usd)
            ]
            
            if include_skills:
                row.extend([
                    f'"{"; ".join(result.matched_skills)}"',
                    f'"{"; ".join(result.missing_skills)}"',
                    f'"{"; ".join(result.strengths)}"',
                    f'"{"; ".join(result.weaknesses)}"'
                ])
            
            if include_feedback and result.feedback_message:
                # Escape quotes and newlines for CSV
                feedback = result.feedback_message.replace('"', '""').replace('\n', ' ')
                row.append(f'"{feedback}"')
            
            csv_lines.append(",".join(row))
        
        return "\n".join(csv_lines)
    
    def export_to_json(
        self,
        results: Optional[List[ScreeningResult]] = None
    ) -> str:
        """
        Export results to JSON format.
        
        Args:
            results: Results to export (uses all if None)
            
        Returns:
            JSON string
        """
        import json
        
        if results is None:
            results = self.db.get_all_results()
        
        # Convert to dicts
        data = [result.model_dump() for result in results]
        
        return json.dumps(data, indent=2, default=str)
    
    def _filter_by_time(
        self,
        time_range: Optional[TimeRange]
    ) -> List[ScreeningResult]:
        """Filter results by time range using database service."""
        time_range_str = time_range.value if time_range else None
        return self.db.get_all_results(time_range=time_range_str)


# Global instance
analytics_service = AnalyticsService()
