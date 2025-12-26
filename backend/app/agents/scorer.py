"""
Scorer Agent - Makes hiring decisions based on match scores.

This is a DETERMINISTIC RULE-BASED agent that applies configurable thresholds
to match scores to make hiring decisions. No LLM needed - pure logic!

Design Philosophy:
- Hiring decisions should be consistent and explainable
- Use clear, configurable thresholds (not black-box AI)
- Provide detailed reasoning for audit trails
- Flag borderline cases for human review

Decision Logic:
- score >= hire_threshold (75) → HIRE
- reject_threshold (50) < score < hire_threshold → MAYBE
- score <= reject_threshold → REJECT

Why Deterministic?
1. Consistency: Same score = same decision (critical for fairness)
2. Transparency: Clear rules, not AI mystery
3. Compliance: Auditable decisions for HR regulations
4. Performance: 0ms processing, $0 cost
"""

import logging
from typing import List
from app.schemas.matching import MatchResult, MatchLevel
from app.schemas.scoring import (
    Decision,
    ConfidenceLevel,
    DecisionResult,
    DecisionReasoning,
    ThresholdConfig
)

logger = logging.getLogger(__name__)


class ScorerAgent:
    """
    Agent that makes hiring decisions based on match scores.
    
    This agent takes the output from Phase 6 (MatchResult) and applies
    configurable thresholds to make a hiring decision.
    
    Key Features:
    - Configurable thresholds (hire_threshold, reject_threshold)
    - Confidence calculation based on distance from thresholds
    - Detailed reasoning generation
    - Human review flagging for borderline cases
    """
    
    def __init__(self, thresholds: ThresholdConfig = None):
        """
        Initialize the Scorer Agent.
        
        Args:
            thresholds: Optional custom thresholds (uses defaults if not provided)
        """
        self.thresholds = thresholds or ThresholdConfig()
        self.thresholds.validate()
        
        logger.info(
            f"Scorer Agent initialized with thresholds: "
            f"HIRE >= {self.thresholds.hire_threshold}, "
            f"REJECT <= {self.thresholds.reject_threshold}"
        )
    
    def process(self, match_result: MatchResult) -> DecisionResult:
        """
        Make a hiring decision based on match results.
        
        Args:
            match_result: The matching results from Phase 6
            
        Returns:
            DecisionResult with decision, confidence, and reasoning
        """
        logger.info(f"Scoring candidate with overall score: {match_result.overall_score}")
        
        # 1. Determine decision based on thresholds
        decision = self._determine_decision(match_result.overall_score)
        
        # 2. Calculate confidence level
        confidence = self._calculate_confidence(
            match_result.overall_score,
            decision
        )
        
        # 3. Generate detailed reasoning
        reasoning = self._generate_reasoning(match_result, decision)
        
        # 4. Determine if human review is needed
        requires_review = self._requires_human_review(
            decision,
            confidence,
            match_result
        )
        
        # 5. Set review priority
        review_priority = self._calculate_review_priority(
            decision,
            confidence,
            match_result
        )
        
        # 6. Generate next steps
        next_steps = self._generate_next_steps(
            decision,
            match_result
        )
        
        result = DecisionResult(
            decision=decision,
            confidence=confidence,
            overall_score=match_result.overall_score,
            thresholds_used=self.thresholds,
            reasoning=reasoning,
            requires_human_review=requires_review,
            review_priority=review_priority,
            next_steps=next_steps
        )
        
        logger.info(
            f"Decision: {decision.value.upper()} "
            f"(confidence: {confidence.value}, "
            f"review needed: {requires_review})"
        )
        
        return result
    
    def _determine_decision(self, score: float) -> Decision:
        """
        Apply threshold logic to determine decision.
        
        Logic:
        - score >= hire_threshold → HIRE
        - reject_threshold < score < hire_threshold → MAYBE
        - score <= reject_threshold → REJECT
        """
        if score >= self.thresholds.hire_threshold:
            return Decision.HIRE
        elif score > self.thresholds.reject_threshold:
            return Decision.MAYBE
        else:
            return Decision.REJECT
    
    def _calculate_confidence(self, score: float, decision: Decision) -> ConfidenceLevel:
        """
        Calculate confidence based on distance from threshold boundaries.
        
        High confidence: Far from boundaries (10+ points)
        Medium confidence: Moderate distance (5-10 points)
        Low confidence: Near boundaries (<5 points)
        """
        hire_threshold = self.thresholds.hire_threshold
        reject_threshold = self.thresholds.reject_threshold
        
        if decision == Decision.HIRE:
            # How far above hire threshold?
            distance = score - hire_threshold
            if distance >= 10:
                return ConfidenceLevel.HIGH
            elif distance >= 5:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW
        
        elif decision == Decision.REJECT:
            # How far below reject threshold?
            distance = reject_threshold - score
            if distance >= 10:
                return ConfidenceLevel.HIGH
            elif distance >= 5:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW
        
        else:  # MAYBE
            # How centered in the MAYBE range?
            maybe_range_midpoint = (hire_threshold + reject_threshold) / 2
            distance_from_midpoint = abs(score - maybe_range_midpoint)
            
            # Closer to midpoint = higher confidence in MAYBE
            if distance_from_midpoint <= 5:
                return ConfidenceLevel.HIGH
            elif distance_from_midpoint <= 10:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW
    
    def _generate_reasoning(
        self,
        match_result: MatchResult,
        decision: Decision
    ) -> DecisionReasoning:
        """Generate detailed reasoning for the decision."""
        
        primary_factors = []
        supporting_evidence = []
        concerns = []
        edge_cases = []
        
        # Primary factor: Score and threshold
        score = match_result.overall_score
        primary_factors.append(
            f"Overall match score of {score:.1f}% results in {decision.value.upper()} decision"
        )
        
        # Decision-specific factors
        if decision == Decision.HIRE:
            primary_factors.append(
                f"Score exceeds hire threshold of {self.thresholds.hire_threshold}%"
            )
            primary_factors.append(
                f"Candidate demonstrates {match_result.match_level.value} match"
            )
        elif decision == Decision.REJECT:
            primary_factors.append(
                f"Score below reject threshold of {self.thresholds.reject_threshold}%"
            )
            primary_factors.append(
                f"Significant skill gaps identified"
            )
        else:  # MAYBE
            primary_factors.append(
                f"Score in borderline range ({self.thresholds.reject_threshold}-{self.thresholds.hire_threshold}%)"
            )
            primary_factors.append(
                f"Mixed strengths and weaknesses require evaluation"
            )
        
        # Supporting evidence from match result
        if match_result.required_skills_match_percent >= 80:
            supporting_evidence.append(
                f"Strong required skills match: {match_result.required_skills_match_percent:.1f}%"
            )
        elif match_result.required_skills_match_percent >= 50:
            supporting_evidence.append(
                f"Moderate required skills match: {match_result.required_skills_match_percent:.1f}%"
            )
        else:
            concerns.append(
                f"Low required skills match: {match_result.required_skills_match_percent:.1f}%"
            )
        
        if match_result.experience_match.is_sufficient:
            supporting_evidence.append(
                f"Experience requirement met: {match_result.experience_match.candidate_total_years} years"
            )
        else:
            concerns.append(
                f"Insufficient experience: {match_result.experience_match.candidate_total_years} years "
                f"(requires {match_result.experience_match.job_min_years})"
            )
        
        if match_result.education_match.meets_requirement:
            supporting_evidence.append(
                f"Education requirement met: {match_result.education_match.candidate_highest_degree}"
            )
        else:
            concerns.append(
                f"Education below requirement: {match_result.education_match.candidate_highest_degree} "
                f"(requires {match_result.education_match.job_required_degree})"
            )
        
        # Add top strengths and weaknesses
        if match_result.key_strengths:
            supporting_evidence.extend(match_result.key_strengths[:3])
        
        if match_result.key_weaknesses:
            concerns.extend(match_result.key_weaknesses[:3])
        
        # Edge cases
        if match_result.experience_match.is_overqualified:
            edge_cases.append(
                f"Candidate may be overqualified: {match_result.experience_match.candidate_total_years} years "
                f"for {match_result.experience_match.job_min_years}-year role"
            )
        
        # Check for critical skill gaps
        critical_gaps = match_result.missing_required_skills[:3]
        if critical_gaps:
            concerns.append(
                f"Missing {len(critical_gaps)} critical skills: "
                f"{', '.join([g.skill_name for g in critical_gaps])}"
            )
        
        return DecisionReasoning(
            primary_factors=primary_factors,
            supporting_evidence=supporting_evidence,
            concerns=concerns,
            edge_cases=edge_cases
        )
    
    def _requires_human_review(
        self,
        decision: Decision,
        confidence: ConfidenceLevel,
        match_result: MatchResult
    ) -> bool:
        """
        Determine if this candidate needs human review.
        
        Review needed when:
        - Decision is MAYBE (always review borderline cases)
        - Low confidence in any decision
        - Significant edge cases (overqualified, critical gaps with high score)
        """
        # Always review MAYBE decisions
        if decision == Decision.MAYBE:
            return True
        
        # Review low confidence decisions
        if confidence == ConfidenceLevel.LOW:
            return True
        
        # Review if overqualified
        if match_result.experience_match.is_overqualified:
            return True
        
        # Review if high score but critical skill gaps
        if match_result.overall_score >= 70:
            if match_result.missing_required_skills:
                return True
        
        return False
    
    def _calculate_review_priority(
        self,
        decision: Decision,
        confidence: ConfidenceLevel,
        match_result: MatchResult
    ) -> str:
        """
        Calculate priority level for human review.
        
        High priority: MAYBE decisions near hire threshold, low confidence HIREs
        Medium priority: MAYBE decisions in middle range, edge cases
        Low priority: Clear decisions with high confidence
        """
        # High priority cases
        if decision == Decision.MAYBE:
            if match_result.overall_score >= 70:
                return "high"  # Close to hire threshold
        
        if decision == Decision.HIRE and confidence == ConfidenceLevel.LOW:
            return "high"  # Uncertain hire decision
        
        # Medium priority cases
        if decision == Decision.MAYBE:
            return "medium"  # All other MAYBE cases
        
        if confidence == ConfidenceLevel.LOW:
            return "medium"  # Any low confidence decision
        
        if match_result.experience_match.is_overqualified:
            return "medium"  # Overqualified candidates
        
        # Low priority (clear decisions)
        return "low"
    
    def _generate_next_steps(
        self,
        decision: Decision,
        match_result: MatchResult
    ) -> List[str]:
        """Generate recommended next actions based on decision."""
        
        next_steps = []
        
        if decision == Decision.HIRE:
            next_steps.append("Proceed to technical interview")
            next_steps.append("Verify skill claims through practical assessment")
            
            # Mention any areas to probe
            if match_result.missing_required_skills or match_result.missing_preferred_skills:
                top_gaps = [g.skill_name for g in (match_result.missing_required_skills + match_result.missing_preferred_skills)[:2]]
                next_steps.append(
                    f"Ask about experience with: {', '.join(top_gaps)}"
                )
        
        elif decision == Decision.REJECT:
            next_steps.append("Send rejection notification with feedback")
            
            # Suggest improvement areas
            if match_result.missing_required_skills:
                critical_gaps = [g.skill_name for g in match_result.missing_required_skills[:3]]
                if critical_gaps:
                    next_steps.append(
                        f"Suggest developing skills: {', '.join(critical_gaps)}"
                    )
            
            next_steps.append("Consider for future roles if skills improve")
        
        else:  # MAYBE
            next_steps.append("Schedule phone screen for detailed evaluation")
            next_steps.append("Human review required before proceeding")
            
            # Focus areas for interview
            if match_result.missing_required_skills or match_result.missing_preferred_skills:
                gaps = [g.skill_name for g in (match_result.missing_required_skills + match_result.missing_preferred_skills)[:3]]
                next_steps.append(
                    f"Assess learning ability and interest in: {', '.join(gaps)}"
                )
            
            if match_result.key_weaknesses:
                next_steps.append(
                    f"Discuss concerns: {match_result.key_weaknesses[0]}"
                )
        
        return next_steps
