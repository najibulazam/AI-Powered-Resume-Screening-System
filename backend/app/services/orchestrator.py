"""
Orchestrator service - coordinates the complete screening pipeline.

This service runs all 5 agents in sequence and handles errors, retries,
and progress tracking.
"""

import logging
import uuid
import time
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from app.agents.resume_parser import ResumeParserAgent
from app.agents.job_analyzer import JobAnalyzerAgent
from app.agents.skill_matcher import SkillMatcherAgent
from app.agents.scorer import ScorerAgent
from app.agents.feedback_generator import FeedbackGeneratorAgent
from app.schemas.orchestration import (
    ScreeningJob, JobStatus, ScreeningResult, ScreeningConfig
)
from app.schemas.scoring import ThresholdConfig
from app.utils.file_handler import FileHandler

logger = logging.getLogger(__name__)


class ScreeningOrchestrator:
    """
    Coordinates the complete candidate screening pipeline.
    
    Pipeline: Resume Parse -> Job Analyze -> Match -> Score -> Feedback
    
    Responsibilities:
    - Sequential agent execution
    - Error handling and retry logic
    - Progress tracking
    - Cost and performance monitoring
    """
    
    def __init__(self, file_handler: FileHandler):
        """Initialize orchestrator with agent instances."""
        self.file_handler = file_handler
        
        # Initialize all agents
        self.resume_agent = ResumeParserAgent()
        self.job_agent = JobAnalyzerAgent()
        self.matcher_agent = SkillMatcherAgent()
        self.scorer_agent = ScorerAgent()
        self.feedback_agent = FeedbackGeneratorAgent()
        
        # Phase weights for progress calculation
        self.phase_weights = {
            JobStatus.PARSING: 20,         # 20% when parsing starts
            JobStatus.EXTRACTING: 40,      # 40% when extraction starts
            JobStatus.MATCHING: 60,        # 60% when matching starts
            JobStatus.SCORING: 80,         # 80% when scoring starts
            JobStatus.GENERATING_FEEDBACK: 90,  # 90% when feedback starts
            JobStatus.COMPLETED: 100       # 100% when done
        }
        
        # Cost tracking (per phase, in USD)
        self.phase_costs = {
            "parsing": 0.0,
            "resume_extraction": 0.002,
            "job_extraction": 0.002,
            "matching": 0.0,
            "scoring": 0.0,
            "feedback": 0.003
        }
    
    async def screen_candidate(
        self,
        resume_file_id: str,
        job_file_id: str,
        config: Optional[ScreeningConfig] = None
    ) -> ScreeningJob:
        """
        Run complete screening pipeline for a single candidate.
        
        Args:
            resume_file_id: Resume file UUID
            job_file_id: Job description file UUID
            config: Optional screening configuration
            
        Returns:
            ScreeningJob with complete results
        """
        # Use default config if none provided
        if config is None:
            config = ScreeningConfig()
        
        # Create job tracking
        job_id = str(uuid.uuid4())
        job = ScreeningJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            resume_file_id=resume_file_id,
            job_file_id=job_file_id,
            started_at=datetime.now()
        )
        
        logger.info(f"Starting screening job {job_id}")
        start_time = time.time()
        total_cost = 0.0
        
        try:
            # Phase 1: Parse resume and job description
            job.status = JobStatus.PARSING
            job.current_phase = "Parsing documents"
            job.progress_percent = self.phase_weights[JobStatus.PARSING]
            
            # Get file paths
            resume_path = self.file_handler.get_file_path(resume_file_id, "resume")
            job_path = self.file_handler.get_file_path(job_file_id, "job_description")
            
            if not resume_path or not job_path:
                raise ValueError("File not found")
            
            resume_text = self._extract_text(str(resume_path))
            job_text = self._extract_text(str(job_path))
            
            # Phase 2: AI Extraction (Resume)
            job.status = JobStatus.EXTRACTING
            job.current_phase = "Extracting resume data"
            job.progress_percent = self.phase_weights[JobStatus.EXTRACTING]
            
            resume_response = self.resume_agent.process(resume_text)
            total_cost += self.phase_costs["resume_extraction"]
            
            # Check for errors
            if not resume_response.success or not resume_response.resume_data:
                raise ValueError(f"Resume parsing failed: {resume_response.error_message}")
            
            # Phase 3: AI Extraction (Job)
            job.current_phase = "Analyzing job requirements"
            
            job_response = self.job_agent.process(job_text)
            total_cost += self.phase_costs["job_extraction"]
            
            # Check for errors
            if not job_response.success or not job_response.job_data:
                raise ValueError(f"Job parsing failed: {job_response.error_message}")
            
            # Phase 4: Skill Matching
            job.status = JobStatus.MATCHING
            job.current_phase = "Matching skills and experience"
            job.progress_percent = self.phase_weights[JobStatus.MATCHING]
            
            # Pass extracted data to matcher
            match_response = self.matcher_agent.process(
                resume_response.resume_data,
                job_response.job_data
            )
            total_cost += self.phase_costs["matching"]
            
            # Extract match result from response
            if not match_response.success or not match_response.match_result:
                raise ValueError(f"Matching failed: {match_response.error_message}")
            
            match_result = match_response.match_result
            
            # Phase 5: Scoring & Decision
            job.status = JobStatus.SCORING
            job.current_phase = "Scoring candidate"
            job.progress_percent = self.phase_weights[JobStatus.SCORING]
            
            # Apply custom thresholds if provided
            thresholds = ThresholdConfig(
                hire_threshold=config.hire_threshold,
                reject_threshold=config.reject_threshold
            )
            
            # Create scorer with custom thresholds
            scorer = ScorerAgent(thresholds=thresholds)
            decision_result = scorer.process(match_result)
            total_cost += self.phase_costs["scoring"]
            
            # Phase 6: Feedback Generation (optional)
            feedback_message = None
            if config.generate_feedback:
                job.status = JobStatus.GENERATING_FEEDBACK
                job.current_phase = "Generating feedback"
                job.progress_percent = self.phase_weights[JobStatus.GENERATING_FEEDBACK]
                
                # Pass decision_result and candidate name
                feedback_result = self.feedback_agent.process(
                    decision_result=decision_result,
                    candidate_name=resume_response.resume_data.full_name,
                    job_title="the position",
                    include_score=config.include_scores
                )
                total_cost += self.phase_costs["feedback"]
                
                # Check for errors
                if not feedback_result.success or not feedback_result.feedback:
                    logger.warning(f"Feedback generation failed: {feedback_result.error}")
                else:
                    # Combine feedback sections
                    feedback_message = self._format_feedback(
                        feedback_result.feedback,
                        match_result.overall_score if config.include_scores else None
                    )
            
            # Complete!
            job.status = JobStatus.COMPLETED
            job.current_phase = "Complete"
            job.progress_percent = 100
            job.completed_at = datetime.now()
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build result
            job.result = ScreeningResult(
                candidate_name=resume_response.resume_data.full_name,
                resume_file_id=resume_file_id,
                job_file_id=job_file_id,
                overall_score=match_result.overall_score,
                decision=decision_result.decision.value,
                confidence=decision_result.confidence,
                matched_skills=[m.skill_name for m in match_result.matched_required_skills],
                missing_skills=[g.skill_name for g in match_result.missing_required_skills],
                strengths=match_result.key_strengths,
                weaknesses=match_result.key_weaknesses,
                feedback_message=feedback_message,
                requires_human_review=decision_result.requires_human_review,
                review_priority=decision_result.review_priority,
                processing_time_ms=processing_time_ms,
                cost_usd=total_cost
            )
            
            logger.info(
                f"Screening job {job_id} completed: "
                f"{decision_result.decision.value} ({processing_time_ms:.0f}ms, ${total_cost:.4f})"
            )
            
            # Add result to analytics (for Phase 10)
            from app.services.analytics import analytics_service
            await analytics_service.add_result(job.result)
            
        except Exception as e:
            logger.error(f"Screening job {job_id} failed: {str(e)}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.error_phase = job.current_phase
            job.completed_at = datetime.now()
        
        return job
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from file (PDF or TXT)."""
        if file_path.lower().endswith('.pdf'):
            return self._extract_pdf_text(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        import PyPDF2
        
        text = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        return '\n'.join(text)
    
    def _format_feedback(
        self,
        feedback,
        score: Optional[float] = None
    ) -> str:
        """Format feedback into a readable message."""
        sections = []
        
        # Opening
        if feedback.opening_message:
            sections.append(feedback.opening_message)
        
        # Score (optional)
        if score is not None:
            sections.append(f"\nYour overall match score: {score:.1f}/100")
        
        # Strengths
        if feedback.strengths_summary:
            sections.append(f"\nYour Strengths:\n{feedback.strengths_summary}")
        
        # Improvements
        if feedback.areas_for_improvement:
            sections.append(f"\nAreas for Growth:\n{feedback.areas_for_improvement}")
        
        # Recommendations
        if feedback.skill_recommendations:
            sections.append("\nOur Recommendations:")
            for rec in feedback.skill_recommendations:
                sections.append(f"- {rec}")
        
        # Next steps
        if feedback.next_steps:
            sections.append("\nNext Steps:")
            for step in feedback.next_steps:
                sections.append(f"- {step}")
        
        # Closing
        if feedback.closing_message:
            sections.append(f"\n{feedback.closing_message}")
        
        return "\n".join(sections)
    
    async def screen_batch(
        self,
        job_file_id: str,
        resume_file_ids: List[str],
        config: Optional[ScreeningConfig] = None
    ) -> Tuple[str, List[ScreeningJob]]:
        """
        Screen multiple candidates for the same job.
        
        Args:
            job_file_id: Job description file UUID
            resume_file_ids: List of resume file UUIDs
            config: Optional screening configuration
            
        Returns:
            Tuple of (batch_id, list of ScreeningJob results)
        """
        batch_id = str(uuid.uuid4())
        logger.info(
            f"Starting batch screening {batch_id} "
            f"({len(resume_file_ids)} candidates)"
        )
        
        jobs = []
        for resume_file_id in resume_file_ids:
            job = await self.screen_candidate(resume_file_id, job_file_id, config)
            jobs.append(job)
        
        # Summary
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        
        logger.info(
            f"Batch {batch_id} complete: "
            f"{completed} succeeded, {failed} failed"
        )
        
        return batch_id, jobs
    
    def get_batch_summary(self, jobs: List[ScreeningJob]) -> Dict:
        """Generate summary statistics for a batch."""
        total = len(jobs)
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        pending = total - completed - failed
        
        # Decision breakdown (for completed jobs)
        decisions = {"HIRE": 0, "MAYBE": 0, "REJECT": 0}
        total_cost = 0.0
        total_time = 0.0
        
        for job in jobs:
            if job.result:
                # Normalize decision to uppercase
                decision = job.result.decision.upper()
                if decision in decisions:
                    decisions[decision] += 1
                total_cost += job.result.cost_usd
                total_time += job.result.processing_time_ms
        
        return {
            "total_jobs": total,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "pending_jobs": pending,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "decisions_summary": decisions,
            "total_cost_usd": total_cost,
            "average_time_ms": total_time / completed if completed > 0 else 0
        }
