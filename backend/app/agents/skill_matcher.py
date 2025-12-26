"""
Skill Matcher Agent

WHY THIS AGENT:
- Compares ResumeSchema vs JobDescriptionSchema
- Calculates match scores and skill gaps
- MOSTLY DETERMINISTIC (less LLM, more logic)
- Bridge between extraction (Phases 4-5) and decision (Phases 7-8)

AGENT RESPONSIBILITY:
Input: ResumeSchema + JobDescriptionSchema
Output: MatchResult (scores, gaps, recommendations)

KEY DIFFERENCE FROM PREVIOUS AGENTS:
- Resume Parser & Job Analyzer: Heavy LLM (extraction)
- Skill Matcher: Light LLM (mostly set operations and calculations)
- Why? Matching is deterministic - no need for expensive LLM!

INTERVIEW POINT:
"I designed the Skill Matcher as a hybrid agent - it does deterministic
matching (set intersections, percentage calculations) but uses LLM for
semantic similarity on skill names. For example, 'JavaScript' and 'JS'
should match. This hybrid approach is cost-effective - only use expensive
LLM where needed, not for everything."
"""

import time
from typing import List, Set, Optional, Dict
from datetime import datetime

from app.schemas.resume import ResumeSchema
from app.schemas.job_description import JobDescriptionSchema, SkillRequirement
from app.schemas.matching import (
    MatchResult,
    MatchResponse,
    SkillMatch,
    SkillGap,
    ExperienceMatch,
    EducationMatch,
    MatchLevel
)


class SkillMatcherAgent:
    """
    Skill Matcher Agent - compares resume vs job description.
    
    ARCHITECTURE DECISION:
    This agent is MOSTLY DETERMINISTIC:
    - Skill overlap: Set operations (intersection, difference)
    - Percentages: Simple math (matched / total * 100)
    - Experience fit: Numeric comparison
    
    WHY NOT USE LLM FOR EVERYTHING:
    - Cost: LLM calls are $0.002+ each
    - Speed: Set operations are microseconds vs LLM is seconds
    - Accuracy: Math is 100% accurate, LLM can hallucinate
    - Determinism: Same input = same output (important for testing)
    
    WHEN WE COULD ADD LLM (Future enhancement):
    - Semantic similarity: "React" matches "ReactJS", "React.js"
    - Skill inference: "Built REST APIs" implies "knows HTTP"
    - Responsibility matching: Compare job duties vs experience
    
    FOR NOW: Simple string matching (case-insensitive)
    LATER (Phase 10): Add embedding-based similarity
    """
    
    def __init__(self):
        """
        Initialize Skill Matcher Agent.
        
        NO LLM CLIENT:
        This agent is primarily deterministic logic.
        Could add embedding model later for semantic matching.
        """
        pass
    
    def _normalize_skill(self, skill: str) -> str:
        """
        Normalize skill name for matching.
        
        HANDLES:
        - Case: "Python" == "python"
        - Whitespace: " Python " == "Python"
        - Common variations: Could expand later
        
        FUTURE:
        - "JavaScript" == "JS" (need mapping or embeddings)
        - "React.js" == "ReactJS" == "React"
        """
        return skill.lower().strip()
    
    def _calculate_skill_matches(
        self,
        candidate_skills: List[str],
        job_skills: List[SkillRequirement]
    ) -> tuple[List[SkillMatch], List[SkillGap]]:
        """
        Calculate which skills match and which are missing.
        
        ALGORITHM:
        1. Normalize all skill names (lowercase, trim)
        2. For each job skill, check if candidate has it
        3. Return matches and gaps
        
        WHY RETURN BOTH:
        - Matches: For positive feedback ("You have Python!")
        - Gaps: For improvement feedback ("Learn Docker")
        """
        # Normalize candidate skills for matching
        candidate_skill_set = {self._normalize_skill(s) for s in candidate_skills}
        
        matches = []
        gaps = []
        
        for job_skill in job_skills:
            normalized_job_skill = self._normalize_skill(job_skill.skill_name)
            has_skill = normalized_job_skill in candidate_skill_set
            
            if has_skill:
                # Skill match!
                matches.append(SkillMatch(
                    skill_name=job_skill.skill_name,
                    is_match=True,
                    is_required=job_skill.is_required,
                    candidate_has=True,
                    job_needs=True,
                    years_required=job_skill.years_experience,
                    years_candidate_has=None  # Could infer from work experience
                ))
            else:
                # Skill gap!
                priority = "HIGH" if job_skill.is_required else "MEDIUM"
                reason = f"Required by job" if job_skill.is_required else "Preferred for role"
                
                gaps.append(SkillGap(
                    skill_name=job_skill.skill_name,
                    is_required=job_skill.is_required,
                    priority=priority,
                    reason=reason
                ))
        
        return matches, gaps
    
    def _calculate_experience_match(
        self,
        resume: ResumeSchema,
        job: JobDescriptionSchema
    ) -> ExperienceMatch:
        """
        Check if candidate's experience meets job requirements.
        
        FACTORS:
        - Total years: Does candidate meet minimum?
        - Level: entry vs senior (from schemas)
        - Overqualified: Too much experience can be negative
        
        WHY IMPORTANT:
        - Deal-breaker: 2 years experience for senior role = no
        - Context: 10 years for junior role = overqualified
        """
        candidate_years = resume.total_years_experience or 0
        job_min = job.min_years_experience or 0
        job_max = job.max_years_experience
        
        # Check if meets minimum
        is_sufficient = candidate_years >= job_min
        
        # Check if overqualified (if max specified)
        is_overqualified = False
        if job_max and candidate_years > job_max + 2:  # 2 year buffer
            is_overqualified = True
        
        # Check experience level match
        # Simple for now: just check if sufficient
        # Could enhance: map years to levels (entry/mid/senior)
        experience_level_match = is_sufficient
        
        return ExperienceMatch(
            candidate_total_years=candidate_years,
            job_min_years=job_min,
            job_max_years=job_max,
            is_sufficient=is_sufficient,
            is_overqualified=is_overqualified,
            experience_level_match=experience_level_match
        )
    
    def _calculate_education_match(
        self,
        resume: ResumeSchema,
        job: JobDescriptionSchema
    ) -> EducationMatch:
        """
        Check if candidate's education meets requirements.
        
        SIMPLE FOR NOW:
        - Extract highest degree from resume
        - Compare to job requirement
        - Return boolean
        
        ENHANCEMENT OPPORTUNITY:
        - Field of study matching
        - GPA requirements
        - Relevant coursework
        """
        # Get highest degree (simple heuristic)
        degree_order = {
            "phd": 4,
            "doctorate": 4,
            "master": 3,
            "bachelor": 2,
            "associate": 1,
            "high school": 0
        }
        
        # Extract candidate's highest degree
        highest_degree = None
        highest_level = -1
        for edu in resume.education:
            degree_lower = edu.degree.lower()
            for key, level in degree_order.items():
                if key in degree_lower and level > highest_level:
                    highest_degree = edu.degree
                    highest_level = level
        
        # Get job requirement
        job_required = job.required_education_level
        job_level = -1
        if job_required:
            job_required_lower = job_required.lower()
            for key, level in degree_order.items():
                if key in job_required_lower:
                    job_level = level
                    break
        
        # Check if meets requirement
        meets_requirement = True  # Default to true if no requirement
        if job_level >= 0:
            meets_requirement = highest_level >= job_level
        
        return EducationMatch(
            candidate_highest_degree=highest_degree,
            job_required_degree=job_required,
            meets_requirement=meets_requirement,
            field_matches=True  # Simplified for now
        )
    
    def _calculate_overall_score(
        self,
        required_match_pct: float,
        preferred_match_pct: float,
        experience_match: ExperienceMatch,
        education_match: EducationMatch
    ) -> float:
        """
        Calculate overall match score (0-100).
        
        WEIGHTED FORMULA:
        - Required skills: 50% weight (most important!)
        - Experience fit: 25% weight
        - Preferred skills: 15% weight
        - Education: 10% weight
        
        WHY THESE WEIGHTS:
        - Required skills = deal-breakers
        - Experience = context matters
        - Preferred skills = nice-to-have
        - Education = often flexible
        
        INTERVIEW POINT:
        "I weighted required skills at 50% because they're deal-breakers.
        A candidate with 100% preferred skills but 0% required skills
        scores 15/100 - clearly not a fit. This reflects real hiring
        where 'must-haves' truly matter more than 'nice-to-haves'."
        """
        score = 0.0
        
        # Required skills (50%)
        score += required_match_pct * 0.50
        
        # Experience (25%)
        experience_score = 0.0
        if experience_match.is_sufficient:
            experience_score = 100.0
            if experience_match.is_overqualified:
                experience_score = 75.0  # Penalize overqualification slightly
        else:
            # Partial credit for close matches
            if experience_match.candidate_total_years > 0 and experience_match.job_min_years:
                ratio = experience_match.candidate_total_years / experience_match.job_min_years
                experience_score = min(ratio * 100, 100)
        score += experience_score * 0.25
        
        # Preferred skills (15%)
        score += preferred_match_pct * 0.15
        
        # Education (10%)
        education_score = 100.0 if education_match.meets_requirement else 50.0
        score += education_score * 0.10
        
        return round(score, 2)
    
    def _determine_match_level(self, overall_score: float) -> MatchLevel:
        """Map numeric score to qualitative level"""
        if overall_score >= 90:
            return MatchLevel.EXCELLENT
        elif overall_score >= 75:
            return MatchLevel.STRONG
        elif overall_score >= 60:
            return MatchLevel.GOOD
        elif overall_score >= 40:
            return MatchLevel.FAIR
        else:
            return MatchLevel.WEAK
    
    def _generate_insights(
        self,
        matched_required: List[SkillMatch],
        missing_required: List[SkillGap],
        matched_preferred: List[SkillMatch],
        experience_match: ExperienceMatch,
        education_match: EducationMatch
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Generate strengths, weaknesses, and recommendations.
        
        WHY SEPARATE:
        - Scoring Agent (Phase 7) uses overall score
        - Feedback Agent (Phase 8) uses these insights
        - Different audiences (hiring manager vs candidate)
        """
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Strengths
        if len(matched_required) > 0:
            strengths.append(f"Has {len(matched_required)} required skills")
        if len(matched_preferred) > 0:
            strengths.append(f"Has {len(matched_preferred)} preferred skills (bonus)")
        if experience_match.is_sufficient:
            strengths.append(f"Meets experience requirement ({experience_match.candidate_total_years:.1f} years)")
        if education_match.meets_requirement:
            strengths.append("Meets education requirement")
        
        # Weaknesses
        if len(missing_required) > 0:
            weaknesses.append(f"Missing {len(missing_required)} required skills")
            for gap in missing_required[:3]:  # Top 3
                weaknesses.append(f"Missing: {gap.skill_name}")
        if not experience_match.is_sufficient:
            weaknesses.append(f"Insufficient experience ({experience_match.candidate_total_years:.1f} vs {experience_match.job_min_years} required)")
        if not education_match.meets_requirement:
            weaknesses.append("Does not meet education requirement")
        
        # Recommendations
        if len(missing_required) > 0:
            recommendations.append("Priority: Learn required skills")
            for gap in missing_required[:3]:
                recommendations.append(f"Learn {gap.skill_name} - required by job")
        if not experience_match.is_sufficient:
            recommendations.append("Gain more experience in relevant roles")
        if len(matched_required) > 5 and not experience_match.is_sufficient:
            recommendations.append("Strong skills! Consider highlighting project experience to compensate for years")
        
        return strengths, weaknesses, recommendations
    
    def process(
        self,
        resume: ResumeSchema,
        job: JobDescriptionSchema,
        resume_id: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> MatchResponse:
        """
        Main matching pipeline.
        
        STEPS:
        1. Match required skills
        2. Match preferred skills
        3. Check experience fit
        4. Check education
        5. Calculate scores
        6. Generate insights
        7. Return structured result
        
        DETERMINISTIC:
        Same resume + job = same result (no LLM randomness)
        This is important for testing and consistency.
        """
        start_time = time.time()
        
        try:
            # Step 1: Match required skills
            matched_required, missing_required = self._calculate_skill_matches(
                resume.technical_skills,
                job.required_technical_skills
            )
            
            # Step 2: Match preferred skills
            matched_preferred, missing_preferred = self._calculate_skill_matches(
                resume.technical_skills,
                job.preferred_technical_skills
            )
            
            # Step 3: Calculate percentages
            total_required = len(job.required_technical_skills)
            total_preferred = len(job.preferred_technical_skills)
            
            required_match_pct = (len(matched_required) / total_required * 100) if total_required > 0 else 100.0
            preferred_match_pct = (len(matched_preferred) / total_preferred * 100) if total_preferred > 0 else 100.0
            
            # Step 4: Check experience and education
            experience_match = self._calculate_experience_match(resume, job)
            education_match = self._calculate_education_match(resume, job)
            
            # Step 5: Calculate overall score
            overall_score = self._calculate_overall_score(
                required_match_pct,
                preferred_match_pct,
                experience_match,
                education_match
            )
            
            match_level = self._determine_match_level(overall_score)
            
            # Step 6: Generate insights
            strengths, weaknesses, recommendations = self._generate_insights(
                matched_required,
                missing_required,
                matched_preferred,
                experience_match,
                education_match
            )
            
            # Step 7: Build result
            match_result = MatchResult(
                overall_score=overall_score,
                match_level=match_level,
                required_skills_match_percent=required_match_pct,
                preferred_skills_match_percent=preferred_match_pct,
                matched_required_skills=matched_required,
                missing_required_skills=missing_required,
                matched_preferred_skills=matched_preferred,
                missing_preferred_skills=missing_preferred,
                experience_match=experience_match,
                education_match=education_match,
                key_strengths=strengths,
                key_weaknesses=weaknesses,
                recommendations=recommendations,
                resume_id=resume_id,
                job_id=job_id,
                timestamp=datetime.utcnow().isoformat()
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MatchResponse(
                success=True,
                match_result=match_result,
                processing_time_ms=processing_time
            )
        
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            return MatchResponse(
                success=False,
                error_message=f"Matching error: {str(e)}",
                processing_time_ms=processing_time
            )


# Singleton instance
skill_matcher_agent = SkillMatcherAgent()


# ===========================================
# EDUCATIONAL NOTES
# ===========================================

"""
AGENT DESIGN: Deterministic vs LLM-Based

DETERMINISTIC AGENTS (like Skill Matcher):
- Input → Output mapping is fixed
- Same input always gives same output
- Fast (no API calls)
- Cheap (no LLM costs)
- Testable (predictable)

LLM AGENTS (like Resume Parser):
- Input → Output has variation
- Temperature > 0 means randomness
- Slow (API latency)
- Costly (per-token pricing)
- Harder to test (need error margins)

WHEN TO USE EACH:

Use Deterministic:
- Set operations (skill matching)
- Math (percentages, scores)
- Rules (if-then logic)
- Validation (checks)

Use LLM:
- Extraction (unstructured → structured)
- Generation (feedback text)
- Semantic understanding (context)
- Ambiguity resolution

HYBRID APPROACH:
Many real agents are HYBRID:
- Deterministic core (fast, cheap, reliable)
- LLM enhancements (semantic similarity, edge cases)

Skill Matcher is deterministic core.
COULD ADD LLM for:
- "Python" matches "Python3"
- "React" matches "ReactJS"
- Inferring skills from descriptions

But START SIMPLE. Add complexity only when needed.

INTERVIEW POINT:
"I designed the Skill Matcher as a deterministic agent because skill matching
is fundamentally set operations - intersection and difference. Using an LLM
would be expensive ($0.002 per match) and slower (2 seconds vs microseconds)
for something that doesn't need intelligence. However, I left room for future
enhancement - semantic similarity using embeddings could handle variations
like 'React' vs 'ReactJS'. The key is using the right tool for the job:
deterministic where possible, LLM where necessary."
"""
