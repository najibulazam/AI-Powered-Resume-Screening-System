"""
Job Description Analyzer Agent

WHY THIS AGENT:
- Extracts structured data from job description text
- Separates required vs preferred skills (critical for matching)
- Identifies experience level, seniority, company culture
- Second agent in our multi-agent pipeline

AGENT RESPONSIBILITY:
Input: Clean JD text (from Phase 3 parsing)
Output: JobDescriptionSchema (structured, validated)

NEXT STEP:
Phase 6 will use ResumeSchema + JobDescriptionSchema to match candidates
"""

import json
import time
from typing import Optional
from groq import Groq

from app.config import get_settings
from app.schemas.job_description import (
    JobDescriptionSchema,
    JobAnalyzeResponse,
    ExperienceLevel,
    SkillRequirement
)


class JobAnalyzerAgent:
    """
    Job Description Analyzer Agent.
    
    ARCHITECTURE:
    Similar to Resume Parser, but different domain:
    - Resume: What candidate HAS
    - Job: What company NEEDS
    
    Both produce structured data for matching.
    
    WHY SEPARATE AGENT:
    - Different prompt engineering (JDs have different structure than resumes)
    - Different validation rules
    - Single responsibility principle
    - Can test/replace independently
    
    INTERVIEW POINT:
    "I built separate agents for resume parsing and job analysis even though
    they both do 'extraction'. Why? Different inputs need different prompts.
    JDs emphasize requirements and 'must-haves', while resumes emphasize
    accomplishments. Separating concerns makes each agent better at its job."
    """
    
    def __init__(self):
        """
        Initialize Job Analyzer Agent.
        
        WHY SINGLETON PATTERN:
        - Agent is stateless (no memory between calls)
        - One Groq client per application (efficient)
        - Easy to mock for testing
        """
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.model_name = self.settings.llm_model
    
    def _build_prompt(self, jd_text: str) -> str:
        """
        Build detailed prompt for job description extraction.
        
        PROMPT ENGINEERING:
        1. Role definition (expert recruiter)
        2. Task specification (extract structured data)
        3. JSON schema (exact structure expected)
        4. Extraction rules (how to categorize)
        5. Examples (few-shot learning)
        6. Edge case handling (missing salary, etc.)
        
        KEY DIFFERENCE FROM RESUME PROMPT:
        - Focus on "required" vs "preferred" (JDs are prescriptive)
        - Experience level mapping ("5+ years" → "senior")
        - Responsibility extraction (what they'll DO)
        """
        prompt = f"""You are an expert recruiter analyzing a job description. Extract structured information to match candidates.

**CRITICAL INSTRUCTIONS:**
1. Extract ONLY information explicitly stated in the job description
2. Separate "required" (must-have) from "preferred" (nice-to-have) skills
3. Map experience descriptions to levels: entry (0-2yr), mid (3-5yr), senior (5-8yr), lead (8+yr)
4. For missing fields in lists, use empty arrays []
5. For missing optional text fields, use null
6. Return valid JSON matching this exact structure

**Required JSON Structure:**
{{
  "job_title": "string",
  "company_name": "string or null",
  "department": "string or null",
  "job_type": "full_time|part_time|contract|internship|freelance or null",
  "work_location": "remote|onsite|hybrid or null",
  "location_city": "string or null",
  
  "experience_level": "entry|mid|senior|lead|executive",
  "min_years_experience": integer or null,
  "max_years_experience": integer or null,
  
  "required_technical_skills": [
    {{
      "skill_name": "string",
      "is_required": true,
      "years_experience": integer or null,
      "proficiency_level": "Beginner|Intermediate|Expert or null"
    }}
  ],
  "preferred_technical_skills": [
    {{
      "skill_name": "string",
      "is_required": false,
      "years_experience": integer or null,
      "proficiency_level": "string or null"
    }}
  ],
  "required_soft_skills": ["skill1", "skill2"],
  
  "responsibilities": [
    {{
      "description": "what person will do",
      "is_primary": boolean
    }}
  ],
  
  "required_education_level": "Bachelor's|Master's|PhD|None or null",
  "preferred_education_fields": ["Computer Science", "Engineering"],
  
  "company_size": "Startup|Small|Medium|Large|Enterprise or null",
  "team_size": integer or null,
  "tech_stack": ["tech1", "tech2"],
  
  "salary_range_min": integer or null,
  "salary_range_max": integer or null,
  "benefits": ["benefit1", "benefit2"],
  
  "industry": "string or null",
  "growth_opportunities": ["opportunity1", "opportunity2"]
}}

**Extraction Rules:**

**Skills Categorization:**
- required_technical_skills: Keywords like "must have", "required", "essential", "need"
- preferred_technical_skills: Keywords like "nice to have", "preferred", "bonus", "plus"
- If unclear, default to required (safer for filtering)
- Include years if stated: "5+ years Python" → years_experience: 5

**Experience Level Mapping:**
- "Entry", "Junior", "0-2 years" → "entry"
- "Mid-level", "3-5 years" → "mid"  
- "Senior", "5-8 years" → "senior"
- "Lead", "Staff", "Principal", "8+ years" → "lead"
- "Director", "VP", "C-level" → "executive"

**Responsibilities:**
- Extract bullet points under "Responsibilities", "Duties", "What you'll do"
- is_primary: true for first 3 items or most emphasized

**Salary:**
- Extract numbers from ranges: "$100k-$150k" → min: 100000, max: 150000
- Annual salary only (ignore hourly/monthly)

**Job Description Text:**
{jd_text}

**Output (JSON only, no additional text):**"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Optional[dict]:
        """
        Extract JSON from LLM response.
        
        SAME PATTERN AS RESUME PARSER:
        - Try direct JSON parse
        - Handle markdown wrapping (```json)
        - Handle plain code blocks (```)
        - Return None if unparseable
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Try plain code blocks
            if "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            return None
    
    def process(self, jd_text: str) -> JobAnalyzeResponse:
        """
        Process job description text and extract structured data.
        
        PIPELINE:
        1. Build prompt (detailed instructions)
        2. Call LLM (Groq API)
        3. Parse JSON response
        4. Validate with Pydantic
        5. Return structured response
        
        ERROR HANDLING:
        - API errors → return error response
        - JSON parse errors → return error response
        - Validation errors → return error response
        - Success → return structured job data
        
        WHY RETURN WRAPPER:
        Callers need to know if processing succeeded.
        JobAnalyzeResponse has success flag + error details.
        """
        start_time = time.time()
        
        try:
            # Step 1: Build prompt
            prompt = self._build_prompt(jd_text)
            
            # Step 2: Call LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=3000,  # JDs need more tokens (longer than resumes)
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Step 3: Parse JSON
            job_data = self._parse_llm_response(response_text)
            
            if not job_data:
                return JobAnalyzeResponse(
                    success=False,
                    error_message="Failed to parse JSON from LLM response"
                )
            
            # Step 4: Validate with Pydantic
            try:
                job_schema = JobDescriptionSchema(**job_data)
            except Exception as e:
                return JobAnalyzeResponse(
                    success=False,
                    error_message=f"Validation error: {str(e)}"
                )
            
            # Step 5: Calculate processing time and return
            processing_time = int((time.time() - start_time) * 1000)
            
            # Calculate confidence based on field completeness
            total_fields = 15  # Key fields we care about
            filled_fields = sum([
                1 if job_schema.company_name else 0,
                1 if job_schema.experience_level else 0,
                1 if job_schema.required_technical_skills else 0,
                1 if job_schema.responsibilities else 0,
                1 if job_schema.min_years_experience else 0,
                1 if job_schema.work_location else 0,
                1 if job_schema.job_type else 0,
                1 if job_schema.department else 0,
                1 if job_schema.required_soft_skills else 0,
                1 if job_schema.tech_stack else 0,
                1 if job_schema.salary_range_min else 0,
                1 if job_schema.benefits else 0,
                1 if job_schema.industry else 0,
                1 if job_schema.company_size else 0,
                1 if job_schema.required_education_level else 0,
            ])
            confidence = filled_fields / total_fields
            
            return JobAnalyzeResponse(
                success=True,
                job_data=job_schema,
                confidence_score=confidence,
                processing_time_ms=processing_time
            )
        
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            return JobAnalyzeResponse(
                success=False,
                error_message=f"Agent error: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def process_batch(self, jd_texts: list[str]) -> list[JobAnalyzeResponse]:
        """
        Process multiple job descriptions.
        
        CURRENT: Sequential processing
        FUTURE (Phase 10): Parallel with Celery
        
        WHY SEQUENTIAL NOW:
        - Simple to implement
        - Free tier has rate limits
        - Good enough for testing
        """
        return [self.process(text) for text in jd_texts]


# Singleton instance for application use
job_analyzer_agent = JobAnalyzerAgent()


# ===========================================
# EDUCATIONAL NOTES
# ===========================================

"""
AGENT DESIGN PATTERN: Extraction Agents

Both Resume Parser and Job Analyzer follow the same pattern:

1. __init__: Initialize LLM client
2. _build_prompt: Domain-specific prompt engineering
3. _parse_llm_response: Handle LLM quirks (markdown, etc.)
4. process: Main pipeline (prompt → LLM → parse → validate)
5. process_batch: Handle multiple inputs

WHY THIS PATTERN:
- Consistent across agents (easier to maintain)
- Each agent customizes _build_prompt (domain expertise)
- Shared infrastructure (JSON parsing, error handling)

COULD WE ABSTRACT?
Yes! You could create a base ExtractorAgent class:

class ExtractorAgent(ABC):
    @abstractmethod
    def _build_prompt(self, text: str) -> str:
        pass
    
    def process(self, text: str) -> Response:
        # Common pipeline
        prompt = self._build_prompt(text)
        response = self._call_llm(prompt)
        # ...

class ResumeParserAgent(ExtractorAgent):
    def _build_prompt(self, text: str) -> str:
        # Resume-specific prompt
        
class JobAnalyzerAgent(ExtractorAgent):
    def _build_prompt(self, text: str) -> str:
        # JD-specific prompt

WHEN TO ABSTRACT:
- After 3+ agents (we're at 2, wait for more)
- When pattern stabilizes (might change in Phase 6)
- When duplication hurts (not yet)

"Premature abstraction is the root of complexity" - not Kent Beck, but true!

INTERVIEW POINT:
"I noticed both agents follow the same pattern, but I kept them separate
initially to maintain flexibility. If I had abstracted too early, changes
to one agent would affect the other. Once I have 3-4 agents and the pattern
is stable, then I'd extract a base class. It's about timing - abstract
when patterns emerge, not before."
"""
