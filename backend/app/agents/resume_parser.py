"""
Resume Parser Agent - FIRST AI AGENT!

WHY THIS FILE:
This is where AI enters the system. This agent uses an LLM to extract
structured data from unstructured resume text.

WHAT MAKES THIS AN AGENT:
1. Single responsibility: Parse resumes, nothing else
2. Structured I/O: Takes text, returns ResumeSchema
3. Encapsulated logic: Prompt engineering hidden inside
4. Reusable: Other agents/endpoints can call this
5. Testable: Can mock LLM for unit tests

HOW IT DIFFERS FROM A UTILITY:
- Utility: Deterministic (same input → same output)
- Agent: AI-powered (same input → similar outputs)
- Utility: Fast, free (no API calls)
- Agent: Slower, costs money (LLM API)
"""

import json
import time
from typing import Optional
from groq import Groq

from app.config import get_settings
from app.schemas.resume import ResumeSchema, ResumeParseResponse

settings = get_settings()


class ResumeParserAgent:
    """
    AI agent that extracts structured data from resume text.
    
    ARCHITECTURE:
    - Uses Groq LLaMA for fast, cheap inference
    - JSON mode for structured output
    - Pydantic validation for safety
    - Error handling with fallbacks
    
    PROMPT ENGINEERING:
    The prompt is carefully designed to:
    1. Be clear and specific
    2. Request JSON format
    3. Handle missing fields gracefully
    4. Avoid hallucinations
    """
    
    def __init__(self):
        """
        Initialize agent with LLM client.
        
        WHY GROQ:
        - Free tier: 30 req/min (enough for development)
        - Fast: 100+ tokens/sec (vs OpenAI 50 tokens/sec)
        - LLaMA 70B: Strong reasoning for extraction tasks
        """
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.llm_model
    
    def _build_prompt(self, resume_text: str) -> str:
        """
        Build extraction prompt.
        
        PROMPT ENGINEERING PRINCIPLES:
        1. Clear instruction (what to do)
        2. Output format specification (JSON)
        3. Field descriptions (what each means)
        4. Examples (few-shot learning)
        5. Constraints (handle missing data)
        
        WHY DETAILED PROMPT:
        - Reduces hallucinations (LLM knows what's expected)
        - Improves accuracy (clear instructions)
        - Handles edge cases (missing fields guidance)
        """
        prompt = f"""You are an expert resume parser. Extract structured information from the following resume text.

**IMPORTANT INSTRUCTIONS:**
1. Extract ONLY information that is explicitly stated in the resume
2. Do NOT make up or infer information
3. For missing text fields (email, phone, etc.), use null
4. For missing list fields (skills, certifications, etc.), use empty arrays []
5. Return valid JSON matching this exact structure

**Required JSON Structure:**
{{
  "full_name": "string",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "linkedin_url": "string or null",
  "github_url": "string or null",
  "portfolio_url": "string or null",
  "summary": "string or null",
  "technical_skills": ["skill1", "skill2"],
  "soft_skills": ["skill1", "skill2"],
  "work_experience": [
    {{
      "job_title": "string",
      "company": "string",
      "start_date": "string or null",
      "end_date": "string or null (use 'Present' if current)",
      "duration_months": integer or null,
      "responsibilities": ["resp1", "resp2"],
      "technologies_used": ["tech1", "tech2"]
    }}
  ],
  NOTE: If no work experience found, use empty array []. Do NOT create entries with null job_title or company.
  "total_years_experience": float or null,
  "education": [
    {{
      "degree": "string",
      "field_of_study": "string or null",
      "institution": "string",
      "graduation_year": integer or null,
      "gpa": float or null
    }}
  ],
  NOTE: If no education found, use empty array []. Do NOT create entries with null degree or institution.
  "certifications": ["cert1", "cert2"],
  "languages": ["language1", "language2"],
  "projects": ["project description 1", "project description 2"]
}}

**Extraction Rules:**
- technical_skills: Programming languages, frameworks, tools, databases
- soft_skills: Leadership, communication, teamwork, problem-solving
- total_years_experience: Calculate from work history (approximate is OK)
- duration_months: Estimate if exact dates not given
- Do NOT include page numbers, headers, or formatting artifacts

**Resume Text:**
{resume_text}

**Output (JSON only, no additional text):**"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Optional[dict]:
        """
        Extract JSON from LLM response.
        
        WHY NEEDED:
        LLMs sometimes wrap JSON in markdown or add explanations:
        - "Here's the JSON: ```json {...} ```"
        - "```{...}```"
        - Just the JSON (ideal)
        
        We handle all cases.
        """
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting from markdown code blocks
            if "```json" in response_text:
                # Extract content between ```json and ```
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                # Extract content between ``` and ```
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            else:
                # Could not extract JSON
                return None
    
    def process(self, resume_text: str) -> ResumeParseResponse:
        """
        Main agent method: text in, structured data out.
        
        FLOW:
        1. Build prompt (instructions + resume text)
        2. Call LLM (Groq API)
        3. Parse response (extract JSON)
        4. Validate with Pydantic (ensure correct structure)
        5. Return response (success or error)
        
        ERROR HANDLING:
        - LLM API errors (network, rate limit)
        - JSON parsing errors (malformed output)
        - Validation errors (wrong schema)
        - Each returns informative error message
        """
        start_time = time.time()
        
        try:
            # Build prompt
            prompt = self._build_prompt(resume_text)
            
            # Call LLM
            # WHY THESE PARAMETERS:
            # - temperature=0.1: Low randomness (consistent extraction)
            # - max_tokens=2000: Enough for detailed resume
            # - response_format: JSON mode (forces valid JSON)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume parser that returns valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=2000,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Parse JSON
            resume_dict = self._parse_llm_response(response_text)
            
            if not resume_dict:
                return ResumeParseResponse(
                    success=False,
                    error_message="Failed to parse JSON from LLM response"
                )
            
            # Clean up work experience entries with None values
            if 'work_experience' in resume_dict and resume_dict['work_experience']:
                resume_dict['work_experience'] = [
                    exp for exp in resume_dict['work_experience']
                    if exp and exp.get('job_title') and exp.get('company')
                ]
            
            # Clean up education entries with None values
            if 'education' in resume_dict and resume_dict['education']:
                resume_dict['education'] = [
                    edu for edu in resume_dict['education']
                    if edu and edu.get('degree') and edu.get('institution')
                ]
            
            # Validate with Pydantic
            # WHY IMPORTANT: Even with JSON mode, LLM might return wrong field types
            # Pydantic catches: wrong types, missing required fields, invalid values
            resume_data = ResumeSchema(**resume_dict)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            return ResumeParseResponse(
                success=True,
                resume_data=resume_data,
                confidence_score=0.9,  # Could calculate based on field completeness
                processing_time_ms=processing_time
            )
        
        except json.JSONDecodeError as e:
            return ResumeParseResponse(
                success=False,
                error_message=f"JSON parsing error: {str(e)}"
            )
        
        except Exception as e:
            # Catch all other errors (API errors, validation errors, etc.)
            return ResumeParseResponse(
                success=False,
                error_message=f"Agent error: {str(e)}"
            )
    
    def process_batch(self, resume_texts: list[str]) -> list[ResumeParseResponse]:
        """
        Process multiple resumes.
        
        WHY BATCH METHOD:
        - Process 50 resumes for one job posting
        - Each resume processed independently
        - Errors in one don't affect others
        
        NOTE: This is sequential for now.
        Phase 10 (Celery) will make it parallel.
        """
        results = []
        for resume_text in resume_texts:
            result = self.process(resume_text)
            results.append(result)
        return results


# Singleton instance
# WHY SINGLETON: One client, reused across requests (connection pooling)
resume_parser_agent = ResumeParserAgent()
