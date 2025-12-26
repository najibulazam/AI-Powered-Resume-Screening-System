"""
Feedback Generator Agent - Generates personalized candidate feedback.

This is an LLM-BASED agent that converts structured decision data
into human-friendly feedback messages for candidates.

Design Philosophy:
- Personalized: Address specific strengths and gaps
- Constructive: Focus on growth, not just rejection
- Actionable: Provide concrete next steps
- Empathetic: Understand job search is stressful

Why LLM for Feedback?
- Natural language generation requires creativity
- Need to balance honesty with encouragement
- Personalization based on individual profile
- Tone adaptation (enthusiastic for HIRE, supportive for REJECT)

Cost: ~$0.003 per feedback (LLaMA 70B via Groq)
"""

import json
import logging
from typing import Optional
from groq import Groq

from app.config import get_settings
from app.schemas.scoring import DecisionResult, Decision
from app.schemas.feedback import CandidateFeedback, FeedbackTone, FeedbackSection, FeedbackResponse

settings = get_settings()
logger = logging.getLogger(__name__)


class FeedbackGeneratorAgent:
    """
    Agent that generates personalized feedback for candidates.
    
    Takes structured decision data (Phase 7 output) and converts it
    into human-readable feedback suitable for email notifications.
    
    Key Features:
    - Tone adaptation based on decision (HIRE/MAYBE/REJECT)
    - Specific skill recommendations
    - Encouraging messaging even for rejections
    - Actionable next steps
    """
    
    def __init__(self):
        """Initialize the feedback generator with LLM client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.llm_model
        
        logger.info("Feedback Generator Agent initialized")
    
    def _build_prompt(
        self,
        decision_result: DecisionResult,
        candidate_name: str = "Candidate",
        job_title: str = "the position",
        include_score: bool = False
    ) -> str:
        """
        Build prompt for feedback generation.
        
        Prompt engineering for empathy and constructiveness:
        - Start with gratitude (thank you for applying)
        - Acknowledge strengths first
        - Frame gaps as opportunities
        - End encouragingly
        """
        
        decision = decision_result.decision.value.upper()
        score = decision_result.overall_score
        
        # Extract key information
        primary_factors = "\n".join(f"- {f}" for f in decision_result.reasoning.primary_factors)
        supporting_evidence = "\n".join(f"- {e}" for e in decision_result.reasoning.supporting_evidence)
        concerns = "\n".join(f"- {c}" for c in decision_result.reasoning.concerns) if decision_result.reasoning.concerns else "None"
        next_steps = "\n".join(f"- {s}" for s in decision_result.next_steps)
        
        prompt = f"""You are an empathetic HR professional writing feedback to a job candidate. 
Generate personalized, constructive feedback based on the screening results.

DECISION: {decision}
MATCH SCORE: {score:.1f}%
JOB TITLE: {job_title}
CANDIDATE NAME: {candidate_name}

PRIMARY FACTORS:
{primary_factors}

STRENGTHS:
{supporting_evidence}

AREAS FOR IMPROVEMENT:
{concerns}

NEXT STEPS:
{next_steps}

Generate feedback with this structure (return as JSON):

{{
    "opening_message": "Warm greeting, thank them for applying, state decision clearly but kindly",
    "strengths_summary": "Highlight 2-3 specific strengths from their background. Be genuine and specific.",
    "areas_for_improvement": "If MAYBE/REJECT: Kindly explain skill gaps. Frame as development opportunities. If HIRE: Can be null or brief mention of growth areas.",
    "detailed_feedback": [
        {{
            "title": "Technical Skills",
            "content": "Specific feedback on technical competencies"
        }},
        {{
            "title": "Experience Level",
            "content": "Feedback on years of experience and relevance"
        }}
    ],
    "skill_recommendations": [
        "Specific skill 1 to learn/improve",
        "Specific skill 2 to learn/improve",
        "Specific skill 3 to learn/improve"
    ],
    "next_steps": [
        "What happens next (interview, rejection, further review)",
        "Timeline expectations",
        "Any action items for candidate"
    ],
    "closing_message": "Encouraging closing that leaves candidate feeling valued"
}}

TONE GUIDELINES:
- HIRE: Enthusiastic, welcoming, excited
- MAYBE: Balanced, constructive, hopeful
- REJECT: Supportive, encouraging, focus on growth

KEY PRINCIPLES:
1. Be honest but kind
2. Focus on growth opportunities, not just weaknesses
3. Provide actionable advice
4. Maintain candidate's dignity and motivation
5. Use "we'd love to see" instead of "you're missing"
6. Frame gaps as "opportunities to develop" not "deficiencies"

{f"Include the match score ({score:.1f}%) naturally in the feedback." if include_score else "Do not mention specific numerical scores."}

Return ONLY valid JSON matching the structure above. No markdown formatting.
"""
        
        return prompt
    
    def process(
        self,
        decision_result: DecisionResult,
        candidate_name: str = "Candidate",
        job_title: str = "the position",
        include_score: bool = False
    ) -> FeedbackResponse:
        """
        Generate personalized feedback from decision result.
        
        Args:
            decision_result: The scoring decision from Phase 7
            candidate_name: Candidate's name for personalization
            job_title: Job title for context
            include_score: Whether to include numerical score
            
        Returns:
            FeedbackResponse with generated feedback
        """
        import time
        start_time = time.time()
        
        logger.info(f"Generating feedback for {decision_result.decision.value.upper()} decision")
        
        try:
            # Build prompt
            prompt = self._build_prompt(
                decision_result=decision_result,
                candidate_name=candidate_name,
                job_title=job_title,
                include_score=include_score
            )
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an empathetic HR professional. Generate constructive, encouraging feedback in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,  # Slightly creative for natural language
                max_tokens=1500
            )
            
            # Parse response
            feedback_json = json.loads(response.choices[0].message.content)
            
            # Determine tone
            tone_map = {
                Decision.HIRE: FeedbackTone.ENCOURAGING,
                Decision.MAYBE: FeedbackTone.CONSTRUCTIVE,
                Decision.REJECT: FeedbackTone.SUPPORTIVE
            }
            tone = tone_map.get(decision_result.decision, FeedbackTone.CONSTRUCTIVE)
            
            # Build feedback sections
            detailed_feedback = []
            if "detailed_feedback" in feedback_json:
                for section_data in feedback_json["detailed_feedback"]:
                    detailed_feedback.append(FeedbackSection(
                        title=section_data.get("title", ""),
                        content=section_data.get("content", "")
                    ))
            
            # Create feedback object
            feedback = CandidateFeedback(
                decision=decision_result.decision.value.upper(),
                overall_score=decision_result.overall_score,
                opening_message=feedback_json.get("opening_message", ""),
                strengths_summary=feedback_json.get("strengths_summary", ""),
                areas_for_improvement=feedback_json.get("areas_for_improvement"),
                detailed_feedback=detailed_feedback,
                skill_recommendations=feedback_json.get("skill_recommendations", []),
                next_steps=feedback_json.get("next_steps", []),
                closing_message=feedback_json.get("closing_message", ""),
                tone=tone
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"Feedback generated successfully in {processing_time:.0f}ms")
            
            return FeedbackResponse(
                success=True,
                feedback=feedback,
                processing_time_ms=processing_time
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return FeedbackResponse(
                success=False,
                error=f"Failed to parse feedback: {str(e)}"
            )
        
        except Exception as e:
            logger.error(f"Feedback generation failed: {e}")
            return FeedbackResponse(
                success=False,
                error=f"Feedback generation error: {str(e)}"
            )


# Global instance
feedback_generator_agent = FeedbackGeneratorAgent()
