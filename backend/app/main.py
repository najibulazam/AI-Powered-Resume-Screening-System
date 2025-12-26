"""
Main FastAPI Application

WHY THIS FILE EXISTS:
- Entry point for the entire system
- Coordinates all agents through API endpoints
- In agentic systems, this is the "orchestrator" layer

HOW IT WORKS:
1. User uploads files → API endpoint
2. Endpoint calls agent chain → agents process sequentially
3. Final result returned → user sees decision
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List
from datetime import datetime
from pathlib import Path
import time
import logging

from app.config import get_settings
from app.schemas.upload import (
    JobDescriptionUploadResponse,
    ResumeUploadResponse,
    UploadErrorResponse
)
from app.schemas.parsing import (
    ParsedDocumentResponse,
    BatchParseResponse
)
from app.schemas.resume import (
    ResumeParseRequest,
    ResumeParseResponse
)
from app.schemas.job_description import (
    JobAnalyzeRequest,
    JobAnalyzeResponse
)
from app.schemas.matching import (
    MatchRequest,
    MatchResponse
)
from app.schemas.scoring import (
    ScoringRequest,
    ScoringResponse,
    ThresholdConfig
)
from app.schemas.feedback import (
    FeedbackRequest,
    FeedbackResponse
)
from app.schemas.orchestration import (
    SingleScreeningRequest,
    SingleScreeningResponse,
    BatchScreeningRequest,
    BatchScreeningResponse,
    BatchStatusRequest,
    BatchStatusResponse,
    ScreeningConfig
)
from app.schemas.analytics import (
    DashboardResponse,
    SkillGapRequest,
    SkillGapResponse,
    CostRequest,
    CostResponse,
    ExportRequest,
    ExportResponse,
    TimeRange
)
from app.utils.file_handler import file_handler
from app.utils.pdf_parser import pdf_parser
from app.agents.resume_parser import resume_parser_agent
from app.agents.job_analyzer import job_analyzer_agent
from app.agents.skill_matcher import skill_matcher_agent
from app.agents.scorer import ScorerAgent
from app.agents.feedback_generator import feedback_generator_agent
from app.services.orchestrator import ScreeningOrchestrator
from app.services.analytics import analytics_service

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Agent-Based Resume Screening System",
    description="An autonomous AI-powered resume screening system using multiple specialized agents for intelligent candidate evaluation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Resume Screening API Support",
        "email": "support@resumescreening.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# Production-ready with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)

# Trusted Host Middleware (security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.resumescreening.com", "localhost"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header and logging."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response


# API key authentication (optional)
async def verify_api_key(request: Request):
    """Verify API key if configured."""
    if settings.api_key:
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != settings.api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
    return True


@app.get("/")
async def root():
    """
    Health check endpoint.
    
    WHY: Useful for deployment monitoring and confirming the server is running.
    """
    return {
        "message": "Agent-Based Resume Screening System",
        "status": "operational",
        "environment": settings.environment,
        "agents_available": [
            "resume_parser (Phase 4 ✅)",
            "job_description_analyzer (Phase 5 ✅)",
            "skill_matcher (Phase 6 ✅)",
            "scorer (Phase 7)",
            "feedback_generator (Phase 8)"
        ]
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    response_description="System health status"
)
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
    - API status
    - Configuration status
    - Database connectivity
    - Service versions
    
    Used by:
    - Load balancers for routing decisions
    - Monitoring systems for alerts
    - Docker health checks
    """
    from app.services.database import db_service
    
    # Check database
    db_healthy = False
    db_count = 0
    try:
        if db_service.use_db:
            db_count = db_service.get_count()
            db_healthy = True
    except Exception as e:
        logger.error(f"Health check database error: {e}")
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "up",
            "llm": "configured" if settings.groq_api_key else "not_configured",
            "database": "connected" if db_healthy else ("not_configured" if not db_service.use_db else "error"),
            "redis": "configured" if settings.redis_url else "not_configured"
        },
        "metrics": {
            "total_screenings": db_count,
            "rate_limit_enabled": settings.rate_limit_enabled
        },
        "models": {
            "parsing": settings.parsing_model,
            "scoring": settings.scoring_model,
            "feedback": settings.feedback_model
        }
    }


# ============================================
# UPLOAD ENDPOINTS
# ============================================

@app.post(
    "/api/upload/job-description",
    response_model=JobDescriptionUploadResponse,
    tags=["Upload"],
    summary="Upload job description"
)
@limiter.limit("20/minute")
async def upload_job_description(
    request: Request,
    file: UploadFile = File(..., description="Job description PDF or text file")
):
    """
    Upload a job description file.
    
    WHY THIS ENDPOINT:
    - Separates JD upload from resume upload (single responsibility)
    - Validates file before expensive processing
    - Returns file_id for later reference
    
    AGENTIC FLOW:
    User uploads JD → Save file → Job Analyzer Agent reads it later
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/upload/job-description" \\
         -F "file=@senior_dev.pdf"
    ```
    """
    try:
        # Save file using our utility
        metadata = await file_handler.save_job_description(file)
        
        return JobDescriptionUploadResponse(
            file_id=metadata.file_id,
            filename=metadata.filename,
            file_size=metadata.file_size,
            uploaded_at=metadata.uploaded_at
        )
    
    except HTTPException:
        raise  # Re-raise validation errors
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/upload/resumes",
    response_model=ResumeUploadResponse,
    tags=["Upload"],
    summary="Upload resume files"
)
@limiter.limit("30/minute")
async def upload_resumes(
    request: Request,
    files: List[UploadFile] = File(..., description="Resume PDF files (multiple allowed)")
):
    """
    Upload one or more resume files.
    
    WHY ACCEPT MULTIPLE:
    - HR uploads 20-50 resumes per job posting
    - Batch upload is more efficient than one-by-one
    - All resumes processed against the same JD
    
    AGENTIC FLOW:
    User uploads resumes → Save files → Resume Parser Agent processes each
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/upload/resumes" \\
         -F "files=@resume1.pdf" \\
         -F "files=@resume2.pdf" \\
         -F "files=@resume3.pdf"
    ```
    """
    try:
        # Save all files
        metadata_list = await file_handler.save_resumes(files)
        
        return ResumeUploadResponse(
            file_ids=[m.file_id for m in metadata_list],
            filenames=[m.filename for m in metadata_list],
            total_files=len(metadata_list),
            uploaded_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise  # Re-raise validation errors
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


# ============================================
# PARSING ENDPOINTS
# ============================================

@app.get(
    "/api/parse/job-description/{file_id}",
    response_model=ParsedDocumentResponse,
    tags=["Parsing"],
    summary="Parse job description text"
)
async def parse_job_description(file_id: str):
    """
    Extract and clean text from uploaded job description.
    
    WHY THIS ENDPOINT:
    - Shows users what was extracted before agent processing
    - Validates file is readable
    - NO AI - pure text extraction
    
    AGENTIC CONNECTION:
    This is the bridge between uploaded files and AI agents.
    Agents receive clean text, not raw PDFs.
    
    EXAMPLE:
    ```bash
    curl "http://localhost:8000/api/parse/job-description/jd_20231226_abc123"
    ```
    """
    try:
        # Get file path from file handler
        file_path = file_handler.get_file_path(file_id, "job_description")
        
        # Parse document
        parsed_doc = pdf_parser.parse_document(
            file_path=file_path,
            file_id=file_id,
            filename=file_path.name
        )
        
        # Return response (with text preview to avoid huge responses)
        return ParsedDocumentResponse(
            file_id=parsed_doc.file_id,
            filename=parsed_doc.filename,
            text_preview=parsed_doc.cleaned_text[:500] + "..." if len(parsed_doc.cleaned_text) > 500 else parsed_doc.cleaned_text,
            page_count=parsed_doc.page_count,
            char_count=parsed_doc.char_count,
            word_count=parsed_doc.word_count,
            is_valid=parsed_doc.is_valid,
            validation_errors=parsed_doc.validation_errors
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Job description not found: {file_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parsing error: {str(e)}"
        )


@app.get(
    "/api/parse/resume/{file_id}",
    response_model=ParsedDocumentResponse,
    tags=["Parsing"],
    summary="Parse single resume text"
)
async def parse_resume(file_id: str):
    """
    Extract and clean text from a single resume.
    
    WHY SEPARATE FROM JD:
    - Different validation rules (resumes have different structure)
    - Agents process them differently
    - Easier debugging (know which type failed)
    """
    try:
        # Get file path
        file_path = file_handler.get_file_path(file_id, "resume")
        
        # Parse document
        parsed_doc = pdf_parser.parse_document(
            file_path=file_path,
            file_id=file_id,
            filename=file_path.name
        )
        
        return ParsedDocumentResponse(
            file_id=parsed_doc.file_id,
            filename=parsed_doc.filename,
            text_preview=parsed_doc.cleaned_text[:500] + "..." if len(parsed_doc.cleaned_text) > 500 else parsed_doc.cleaned_text,
            page_count=parsed_doc.page_count,
            char_count=parsed_doc.char_count,
            word_count=parsed_doc.word_count,
            is_valid=parsed_doc.is_valid,
            validation_errors=parsed_doc.validation_errors
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Resume not found: {file_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parsing error: {str(e)}"
        )


@app.post(
    "/api/parse/resumes/batch",
    response_model=BatchParseResponse,
    tags=["Parsing"],
    summary="Parse multiple resumes"
)
async def parse_resumes_batch(file_ids: List[str]):
    """
    Parse multiple resumes in one request.
    
    WHY BATCH:
    - Efficient for processing 50+ resumes
    - Single API call vs 50 calls
    - Parallel processing ready (Phase 10 with Celery)
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/parse/resumes/batch" \\
         -H "Content-Type: application/json" \\
         -d '{"file_ids": ["resume_001", "resume_002"]}'
    ```
    """
    documents = []
    parsed_successfully = 0
    parsing_errors = 0
    
    for file_id in file_ids:
        try:
            # Get file path
            file_path = file_handler.get_file_path(file_id, "resume")
            
            # Parse document
            parsed_doc = pdf_parser.parse_document(
                file_path=file_path,
                file_id=file_id,
                filename=file_path.name
            )
            
            # Track success/failure
            if parsed_doc.is_valid:
                parsed_successfully += 1
            else:
                parsing_errors += 1
            
            # Add to results
            documents.append(ParsedDocumentResponse(
                file_id=parsed_doc.file_id,
                filename=parsed_doc.filename,
                text_preview=parsed_doc.cleaned_text[:500] + "..." if len(parsed_doc.cleaned_text) > 500 else parsed_doc.cleaned_text,
                page_count=parsed_doc.page_count,
                char_count=parsed_doc.char_count,
                word_count=parsed_doc.word_count,
                is_valid=parsed_doc.is_valid,
                validation_errors=parsed_doc.validation_errors
            ))
        
        except FileNotFoundError:
            parsing_errors += 1
            documents.append(ParsedDocumentResponse(
                file_id=file_id,
                filename="unknown",
                text_preview="",
                page_count=0,
                char_count=0,
                word_count=0,
                is_valid=False,
                validation_errors=[f"File not found: {file_id}"]
            ))
        
        except Exception as e:
            parsing_errors += 1
            documents.append(ParsedDocumentResponse(
                file_id=file_id,
                filename="unknown",
                text_preview="",
                page_count=0,
                char_count=0,
                word_count=0,
                is_valid=False,
                validation_errors=[f"Parsing error: {str(e)}"]
            ))
    
    return BatchParseResponse(
        total_files=len(file_ids),
        parsed_successfully=parsed_successfully,
        parsing_errors=parsing_errors,
        documents=documents
    )


# ============================================
# AI AGENT ENDPOINTS
# ============================================

@app.post(
    "/api/agents/parse-resume",
    response_model=ResumeParseResponse,
    tags=["AI Agents"],
    summary="Parse resume with AI (Resume Parser Agent)"
)
async def parse_resume_with_ai(request: ResumeParseRequest):
    """
    Use Resume Parser Agent to extract structured data from resume text.
    
    **THIS IS THE FIRST AI AGENT!**
    
    WHY THIS ENDPOINT:
    - Demonstrates agent usage
    - Separates parsing (deterministic) from extraction (AI)
    - Returns structured, validated JSON
    
    FLOW:
    1. User provides clean text (from Phase 3 parsing)
    2. Resume Parser Agent calls LLM
    3. LLM returns structured JSON
    4. Pydantic validates schema
    5. Return to user
    
    DIFFERENCE FROM PARSING ENDPOINT:
    - Parsing (Phase 3): PDF → Clean Text (deterministic, free, fast)
    - This (Phase 4): Clean Text → Structured JSON (AI, costs $, slower)
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/parse-resume" \\
         -H "Content-Type: application/json" \\
         -d '{"text": "John Doe\\nSenior Engineer\\n..."}'
    ```
    """
    try:
        # Call the Resume Parser Agent
        result = resume_parser_agent.process(request.text)
        return result
    
    except Exception as e:
        return ResumeParseResponse(
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/agents/parse-resume-from-file",
    response_model=ResumeParseResponse,
    tags=["AI Agents"],
    summary="Parse resume from uploaded file (Parse + AI)"
)
async def parse_resume_from_file(file_id: str):
    """
    Complete pipeline: Get file → Parse text → Extract with AI.
    
    WHY CONVENIENT:
    - Single endpoint combines Phase 3 + Phase 4
    - User provides file_id, gets structured JSON
    - Shows full pipeline in action
    
    FLOW:
    1. Get file path from file_id
    2. Parse PDF to clean text (Phase 3 - deterministic)
    3. Extract structured data with AI (Phase 4 - LLM)
    4. Return structured resume
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/parse-resume-from-file?file_id=resume_20231226_abc123"
    ```
    """
    try:
        # Step 1: Get file path
        file_path = file_handler.get_file_path(file_id, "resume")
        
        # Step 2: Parse PDF to text (Phase 3)
        parsed_doc = pdf_parser.parse_document(
            file_path=file_path,
            file_id=file_id,
            filename=file_path.name
        )
        
        # Check if parsing succeeded
        if not parsed_doc.is_valid:
            return ResumeParseResponse(
                success=False,
                error_message=f"PDF parsing failed: {', '.join(parsed_doc.validation_errors)}"
            )
        
        # Step 3: Extract structured data with AI (Phase 4)
        result = resume_parser_agent.process(parsed_doc.cleaned_text)
        
        return result
    
    except FileNotFoundError:
        return ResumeParseResponse(
            success=False,
            error_message=f"Resume file not found: {file_id}"
        )
    
    except Exception as e:
        return ResumeParseResponse(
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/agents/analyze-job-description",
    response_model=JobAnalyzeResponse,
    tags=["AI Agents"],
    summary="Analyze job description with AI (Job Analyzer Agent)"
)
async def analyze_job_description(request: JobAnalyzeRequest):
    """
    Use Job Analyzer Agent to extract structured data from job description text.
    
    **THIS IS THE SECOND AI AGENT!**
    
    WHY THIS ENDPOINT:
    - Extracts what company NEEDS (vs Resume Parser extracts what candidate HAS)
    - Separates required vs preferred skills (critical for matching)
    - Maps experience levels ("5+ years" → "senior")
    - Returns structured, validated JSON
    
    FLOW:
    1. User provides clean JD text (from Phase 3 parsing)
    2. Job Analyzer Agent calls LLM
    3. LLM returns structured JSON
    4. Pydantic validates schema
    5. Return to user
    
    MATCHING PREVIEW:
    Phase 4 gives us ResumeSchema (what candidate has)
    Phase 5 gives us JobDescriptionSchema (what job needs)
    Phase 6 will MATCH them (skills overlap, experience fit)
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/analyze-job-description" \\
         -H "Content-Type: application/json" \\
         -d '{"text": "Senior Engineer needed. 5+ years Python..."}'  
    ```
    """
    try:
        result = job_analyzer_agent.process(request.text)
        return result
    except Exception as e:
        return JobAnalyzeResponse(
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/agents/analyze-job-from-file",
    response_model=JobAnalyzeResponse,
    tags=["AI Agents"],
    summary="Analyze job description from uploaded file (Parse + AI)"
)
async def analyze_job_from_file(file_id: str):
    """
    Complete pipeline: Get JD file → Parse text → Extract with AI.
    
    WHY CONVENIENT:
    - Single endpoint combines Phase 3 + Phase 5
    - User provides file_id, gets structured job data
    - Mirrors parse-resume-from-file pattern
    
    FLOW:
    1. Get file path from file_id
    2. Parse to clean text (Phase 3 - deterministic)
    3. Extract structured data with AI (Phase 5 - LLM)
    4. Return structured job description
    
    USE CASE:
    User uploads JD in Phase 2, gets file_id
    This endpoint converts that file_id into matchable JobDescriptionSchema
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/analyze-job-from-file?file_id=jd_20231226_abc123"
    ```
    """
    try:
        # Step 1: Get file path
        file_path = file_handler.get_file_path(file_id, "job_description")
        
        # Step 2: Parse to text (Phase 3)
        parsed_doc = pdf_parser.parse_document(
            file_path=file_path,
            file_id=file_id,
            filename=file_path.name
        )
        
        # Check if parsing succeeded
        if not parsed_doc.is_valid:
            return JobAnalyzeResponse(
                success=False,
                error_message=f"Parsing failed: {', '.join(parsed_doc.validation_errors)}"
            )
        
        # Step 3: Extract with AI (Phase 5)
        result = job_analyzer_agent.process(parsed_doc.cleaned_text)
        
        return result
    
    except FileNotFoundError:
        return JobAnalyzeResponse(
            success=False,
            error_message=f"Job description file not found: {file_id}"
        )
    
    except Exception as e:
        return JobAnalyzeResponse(
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/agents/match-candidate",
    response_model=MatchResponse,
    tags=["AI Agents"],
    summary="Match candidate to job (Skill Matcher Agent)"
)
async def match_candidate(
    resume_file_id: str,
    job_file_id: str
):
    """
    Use Skill Matcher Agent to compare resume vs job description.
    
    **THIS IS THE THIRD AI AGENT - THE BRIDGE!**
    
    WHY THIS ENDPOINT:
    - Combines Phase 4 (Resume) + Phase 5 (Job) outputs
    - Calculates match scores, skill gaps, recommendations
    - MOSTLY DETERMINISTIC (fast, cheap, consistent)
    - Output feeds into Scoring (Phase 7) and Feedback (Phase 8)
    
    WHAT IT DOES:
    1. Get resume file → parse → extract structured data (Phase 4)
    2. Get job file → parse → extract structured data (Phase 5)
    3. Compare them → calculate matches, gaps, scores (Phase 6)
    4. Return MatchResult with everything downstream agents need
    
    FLOW:
    file_id (resume) + file_id (job)
      ↓
    ResumeSchema + JobDescriptionSchema
      ↓
    MatchResult (scores, gaps, recommendations)
      ↓
    Phase 7: Use overall_score for decision
    Phase 8: Use skill_gaps for feedback
    
    KEY INSIGHT:
    This agent is deterministic (no LLM randomness):
    - Same resume + job = same result
    - Fast: ~50ms (vs 2 seconds for LLM)
    - Cheap: $0 (no LLM calls)
    - Testable: Predictable outputs
    
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/match-candidate?resume_file_id=resume_123&job_file_id=jd_456"
    ```
    
    Returns:
    ```json
    {
      "success": true,
      "match_result": {
        "overall_score": 78.5,
        "match_level": "strong",
        "required_skills_match_percent": 85.7,
        "missing_required_skills": [{"skill_name": "Docker", ...}],
        "key_strengths": ["Has 7 years experience", ...],
        "recommendations": ["Learn Docker", ...]
      }
    }
    ```
    """
    try:
        # Step 1: Get and parse resume
        resume_file_path = file_handler.get_file_path(resume_file_id, "resume")
        resume_parsed = pdf_parser.parse_document(
            file_path=resume_file_path,
            file_id=resume_file_id,
            filename=resume_file_path.name
        )
        
        if not resume_parsed.is_valid:
            return MatchResponse(
                success=False,
                error_message=f"Resume parsing failed: {', '.join(resume_parsed.validation_errors)}"
            )
        
        # Extract structured resume data
        resume_result = resume_parser_agent.process(resume_parsed.cleaned_text)
        if not resume_result.success:
            return MatchResponse(
                success=False,
                error_message=f"Resume extraction failed: {resume_result.error_message}"
            )
        
        # Step 2: Get and parse job description
        job_file_path = file_handler.get_file_path(job_file_id, "job_description")
        job_parsed = pdf_parser.parse_document(
            file_path=job_file_path,
            file_id=job_file_id,
            filename=job_file_path.name
        )
        
        if not job_parsed.is_valid:
            return MatchResponse(
                success=False,
                error_message=f"Job parsing failed: {', '.join(job_parsed.validation_errors)}"
            )
        
        # Extract structured job data
        job_result = job_analyzer_agent.process(job_parsed.cleaned_text)
        if not job_result.success:
            return MatchResponse(
                success=False,
                error_message=f"Job extraction failed: {job_result.error_message}"
            )
        
        # Step 3: Match resume vs job
        match_result = skill_matcher_agent.process(
            resume=resume_result.resume_data,
            job=job_result.job_data,
            resume_id=resume_file_id,
            job_id=job_file_id
        )
        
        return match_result
    
    except FileNotFoundError as e:
        return MatchResponse(
            success=False,
            error_message=f"File not found: {str(e)}"
        )
    
    except Exception as e:
        return MatchResponse(
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )


# ============================================
# SCORING ENDPOINTS (Phase 7)
# ============================================

@app.post(
    "/api/agents/score-candidate",
    response_model=ScoringResponse,
    tags=["Agents"],
    summary="Score candidate and make hiring decision"
)
async def score_candidate(request: ScoringRequest):
    """
    Complete pipeline: Upload → Parse → Extract → Match → Score → Decision
    
    This endpoint runs the full 4-agent chain:
    1. Resume Parser (Phase 4) - Extract structured resume data
    2. Job Analyzer (Phase 5) - Extract structured job requirements
    3. Skill Matcher (Phase 6) - Compare and generate match score
    4. Scorer (Phase 7) - Make hiring decision with thresholds
    
    WHY THIS ENDPOINT:
    - Single API call for complete screening
    - Orchestrates all agents in sequence
    - Returns actionable hiring decision
    
    COST PER CALL:
    - Resume parsing: ~$0.002 (LLM)
    - Job parsing: ~$0.002 (LLM)
    - Skill matching: $0.000 (deterministic)
    - Scoring: $0.000 (deterministic)
    - Total: ~$0.004 per candidate
    
    PROCESSING TIME:
    - ~2-3 seconds (mostly LLM calls)
    - Deterministic steps are instant
    
    Args:
        request: ScoringRequest with file IDs and optional custom thresholds
        
    Returns:
        ScoringResponse with decision (HIRE/MAYBE/REJECT) and reasoning
        
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/score-candidate" \
      -H "Content-Type: application/json" \
      -d '{
        "resume_file_id": "resume_20231226_abc123",
        "job_file_id": "jd_20231226_def456",
        "custom_thresholds": {"hire_threshold": 80, "reject_threshold": 60}
      }'
    ```
    """
    import time
    start_time = time.time()
    
    try:
        # Step 1: Get file paths
        resume_path = file_handler.get_file_path(
            request.resume_file_id,
            "resume"
        )
        job_path = file_handler.get_file_path(
            request.job_file_id,
            "job_description"
        )
        
        # Step 2: Parse documents (extract raw text)
        resume_parsed = pdf_parser.parse_document(
            file_path=resume_path,
            file_id=request.resume_file_id,
            filename=resume_path.name
        )
        
        job_parsed = pdf_parser.parse_document(
            file_path=job_path,
            file_id=request.job_file_id,
            filename=job_path.name
        )
        
        # Step 3: Extract structured data with AI agents
        resume_result = await resume_parser_agent.process(resume_parsed)
        job_result = await job_analyzer_agent.process(job_parsed)
        
        if not resume_result.success:
            return ScoringResponse(
                success=False,
                error=f"Resume parsing failed: {resume_result.error}"
            )
        
        if not job_result.success:
            return ScoringResponse(
                success=False,
                error=f"Job analysis failed: {job_result.error}"
            )
        
        # Step 4: Match resume against job requirements
        match_result = skill_matcher_agent.process(
            resume_schema=resume_result.resume,
            job_schema=job_result.job_description
        )
        
        # Step 5: Score and make decision
        thresholds = request.custom_thresholds or ThresholdConfig()
        scorer = ScorerAgent(thresholds=thresholds)
        decision_result = scorer.process(match_result.match_result)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return ScoringResponse(
            success=True,
            decision_result=decision_result,
            processing_time_ms=processing_time
        )
    
    except FileNotFoundError as e:
        return ScoringResponse(
            success=False,
            error=f"File not found: {str(e)}"
        )
    
    except Exception as e:
        return ScoringResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )


# ============================================
# FEEDBACK ENDPOINTS (Phase 8)
# ============================================

@app.post(
    "/api/agents/generate-feedback",
    response_model=FeedbackResponse,
    tags=["Agents"],
    summary="Generate personalized candidate feedback"
)
async def generate_feedback(request: FeedbackRequest):
    """
    Complete pipeline: Upload -> Parse -> Extract -> Match -> Score -> Feedback
    
    This endpoint runs the full 5-agent chain:
    1. Resume Parser (Phase 4) - Extract structured resume data
    2. Job Analyzer (Phase 5) - Extract structured job requirements
    3. Skill Matcher (Phase 6) - Compare and generate match score
    4. Scorer (Phase 7) - Make hiring decision with thresholds
    5. Feedback Generator (Phase 8) - Create personalized feedback
    
    WHY THIS ENDPOINT:
    - Single API call for complete screening + feedback
    - Generates human-readable feedback for candidates
    - Personalized based on specific strengths/gaps
    - Appropriate tone for HIRE/MAYBE/REJECT
    
    COST PER CALL:
    - Resume parsing: ~$0.002 (LLM)
    - Job parsing: ~$0.002 (LLM)
    - Skill matching: $0.000 (deterministic)
    - Scoring: $0.000 (deterministic)
    - Feedback generation: ~$0.003 (LLM)
    - Total: ~$0.007 per candidate
    
    PROCESSING TIME:
    - ~3-5 seconds (LLM steps)
    
    Args:
        request: FeedbackRequest with file IDs and options
        
    Returns:
        FeedbackResponse with personalized candidate feedback
        
    EXAMPLE:
    ```bash
    curl -X POST "http://localhost:8000/api/agents/generate-feedback" \
      -H "Content-Type: application/json" \
      -d '{
        "resume_file_id": "resume_20231226_abc123",
        "job_file_id": "jd_20231226_def456",
        "include_score_details": false
      }'
    ```
    """
    import time
    start_time = time.time()
    
    try:
        # Step 1: Get file paths
        resume_path = file_handler.get_file_path(
            request.resume_file_id,
            "resume"
        )
        job_path = file_handler.get_file_path(
            request.job_file_id,
            "job_description"
        )
        
        # Step 2: Parse documents
        resume_parsed = pdf_parser.parse_document(
            file_path=resume_path,
            file_id=request.resume_file_id,
            filename=resume_path.name
        )
        
        job_parsed = pdf_parser.parse_document(
            file_path=job_path,
            file_id=request.job_file_id,
            filename=job_path.name
        )
        
        # Step 3: Extract structured data with AI agents
        resume_result = resume_parser_agent.process(resume_parsed)
        job_result = job_analyzer_agent.process(job_parsed)
        
        if not resume_result.success:
            return FeedbackResponse(
                success=False,
                error=f"Resume parsing failed: {resume_result.error_message}"
            )
        
        if not job_result.success:
            return FeedbackResponse(
                success=False,
                error=f"Job analysis failed: {job_result.error_message}"
            )
        
        # Step 4: Match resume against job
        match_result = skill_matcher_agent.process(
            resume=resume_result.resume_data,
            job=job_result.job_data
        )
        
        # Step 5: Score and make decision
        thresholds = ThresholdConfig(**request.custom_thresholds) if request.custom_thresholds else ThresholdConfig()
        scorer = ScorerAgent(thresholds=thresholds)
        decision_result = scorer.process(match_result.match_result)
        
        # Step 6: Generate personalized feedback
        feedback_result = feedback_generator_agent.process(
            decision_result=decision_result,
            candidate_name=resume_result.resume_data.full_name,
            job_title=job_result.job_data.job_title,
            include_score=request.include_score_details
        )
        
        if not feedback_result.success:
            return feedback_result
        
        # Calculate total processing time
        processing_time = (time.time() - start_time) * 1000
        feedback_result.processing_time_ms = processing_time
        
        return feedback_result
    
    except FileNotFoundError as e:
        return FeedbackResponse(
            success=False,
            error=f"File not found: {str(e)}"
        )
    
    except Exception as e:
        return FeedbackResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )


# ============================================
# ORCHESTRATION ENDPOINTS (Phase 9)
# ============================================

# Global orchestrator instance
orchestrator = ScreeningOrchestrator(file_handler)

# In-memory batch tracking (for demo; use Redis/DB in production)
batch_store = {}


@app.post(
    "/api/screen/process",
    response_model=SingleScreeningResponse,
    tags=["Screening"],
    summary="Screen a single candidate (complete pipeline)"
)
@limiter.limit("10/minute")
async def screen_single_candidate(
    request: Request,
    screening_request: SingleScreeningRequest
):
    """
    Run the complete screening pipeline for one candidate.
    
    Pipeline:
    1. Resume parsing (Phase 4)
    2. Job analysis (Phase 5)
    3. Skill matching (Phase 6)
    4. Scoring & decision (Phase 7)
    5. Feedback generation (Phase 8)
    
    Returns:
    - Hiring decision (HIRE/MAYBE/REJECT)
    - Match score and confidence
    - Personalized feedback
    - Processing time and cost
    """
    try:
        # Build config from screening_request
        config = ScreeningConfig(
            hire_threshold=screening_request.custom_thresholds.get("hire", 75.0) if screening_request.custom_thresholds else 75.0,
            reject_threshold=screening_request.custom_thresholds.get("reject", 50.0) if screening_request.custom_thresholds else 50.0,
            generate_feedback=screening_request.include_feedback,
            include_scores=screening_request.include_score_in_feedback
        )
        
        # Run screening
        job = await orchestrator.screen_candidate(
            screening_request.resume_file_id,
            screening_request.job_file_id,
            config
        )
        
        # Check for errors
        if job.status == "FAILED":
            return SingleScreeningResponse(
                success=False,
                job_id=job.job_id,
                error=job.error_message
            )
        
        # Return result
        return SingleScreeningResponse(
            success=True,
            job_id=job.job_id,
            result=job.result
        )
    
    except Exception as e:
        return SingleScreeningResponse(
            success=False,
            job_id="",
            error=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/screen/batch",
    response_model=BatchScreeningResponse,
    tags=["Screening"],
    summary="Screen multiple candidates (batch processing)"
)
async def screen_batch_candidates(request: BatchScreeningRequest):
    """
    Screen multiple candidates for the same job.
    
    Use this for:
    - Processing all applicants for a role
    - Bulk candidate evaluation
    - Automated pre-screening
    
    The system will:
    - Run each candidate through complete pipeline
    - Track progress for each screening
    - Generate summary statistics
    
    Note: This runs sequentially. For production, use async task queue.
    """
    try:
        # Validate batch size
        if len(request.resume_file_ids) > 100:
            return BatchScreeningResponse(
                success=False,
                batch_id="",
                total_candidates=0,
                estimated_completion_seconds=0,
                estimated_cost_usd=0,
                error="Batch size exceeds maximum (100 candidates)"
            )
        
        # Build config
        config = ScreeningConfig(
            hire_threshold=request.custom_thresholds.get("hire", 75.0) if request.custom_thresholds else 75.0,
            reject_threshold=request.custom_thresholds.get("reject", 50.0) if request.custom_thresholds else 50.0,
            generate_feedback=request.include_feedback,
            include_scores=request.include_score_in_feedback
        )
        
        # Estimate time and cost
        num_candidates = len(request.resume_file_ids)
        estimated_time = num_candidates * 5  # ~5 seconds per candidate
        estimated_cost = num_candidates * 0.007  # $0.007 per candidate
        
        # Start batch processing
        batch_id, jobs = await orchestrator.screen_batch(
            request.job_file_id,
            request.resume_file_ids,
            config
        )
        
        # Store in batch store
        batch_store[batch_id] = jobs
        
        # Get job IDs
        job_ids = [job.job_id for job in jobs]
        
        return BatchScreeningResponse(
            success=True,
            batch_id=batch_id,
            total_candidates=num_candidates,
            job_ids=job_ids,
            estimated_completion_seconds=estimated_time,
            estimated_cost_usd=estimated_cost
        )
    
    except Exception as e:
        return BatchScreeningResponse(
            success=False,
            batch_id="",
            total_candidates=0,
            estimated_completion_seconds=0,
            estimated_cost_usd=0,
            error=f"Unexpected error: {str(e)}"
        )


@app.post(
    "/api/screen/batch/status",
    response_model=BatchStatusResponse,
    tags=["Screening"],
    summary="Check batch screening status"
)
async def check_batch_status(request: BatchStatusRequest):
    """
    Check the status of a batch screening operation.
    
    Returns:
    - Overall progress (% complete)
    - Individual job statuses
    - Completed results
    - Summary statistics (HIRE/MAYBE/REJECT counts)
    """
    try:
        # Get batch from store
        jobs = batch_store.get(request.batch_id)
        
        if not jobs:
            return BatchStatusResponse(
                success=False,
                batch_id=request.batch_id,
                total_jobs=0,
                completed_jobs=0,
                failed_jobs=0,
                pending_jobs=0,
                progress_percent=0,
                error="Batch not found"
            )
        
        # Get summary
        summary = orchestrator.get_batch_summary(jobs)
        
        # Collect results
        results = [job.result for job in jobs if job.result is not None]
        
        return BatchStatusResponse(
            success=True,
            batch_id=request.batch_id,
            total_jobs=summary["total_jobs"],
            completed_jobs=summary["completed_jobs"],
            failed_jobs=summary["failed_jobs"],
            pending_jobs=summary["pending_jobs"],
            progress_percent=summary["progress_percent"],
            jobs=jobs,
            results=results,
            decisions_summary=summary["decisions_summary"]
        )
    
    except Exception as e:
        return BatchStatusResponse(
            success=False,
            batch_id=request.batch_id,
            total_jobs=0,
            completed_jobs=0,
            failed_jobs=0,
            pending_jobs=0,
            progress_percent=0,
            error=f"Unexpected error: {str(e)}"
        )


# ============================================
# ANALYTICS ENDPOINTS (Phase 10)
# ============================================

@app.get(
    "/api/analytics/dashboard",
    response_model=DashboardResponse,
    tags=["Analytics"],
    summary="Get dashboard analytics"
)
async def get_dashboard_analytics(time_range: TimeRange = TimeRange.ALL_TIME):
    """
    Get comprehensive dashboard analytics.
    
    Returns:
    - Decision statistics (HIRE/MAYBE/REJECT distribution)
    - Cost analysis (spending breakdown)
    - Performance metrics (timing, success rates)
    - Top skill gaps (most common missing skills)
    
    Use this for:
    - Executive dashboards
    - Progress monitoring
    - Resource planning
    """
    try:
        decision_stats = analytics_service.get_decision_stats(time_range)
        cost_analysis = analytics_service.get_cost_analysis(time_range)
        performance_metrics = analytics_service.get_performance_metrics(time_range)
        skill_gaps = analytics_service.get_skill_gap_analysis(
            time_range=time_range,
            min_frequency=2
        )
        
        return DashboardResponse(
            success=True,
            decision_stats=decision_stats,
            cost_analysis=cost_analysis,
            performance_metrics=performance_metrics,
            top_missing_skills=skill_gaps[:10],  # Top 10
            time_range=time_range.value
        )
    
    except Exception as e:
        return DashboardResponse(
            success=False,
            time_range=time_range.value,
            error=f"Analytics error: {str(e)}"
        )


@app.post(
    "/api/analytics/skills",
    response_model=SkillGapResponse,
    tags=["Analytics"],
    summary="Analyze skill gaps"
)
async def analyze_skill_gaps(request: SkillGapRequest):
    """
    Analyze most common missing skills across candidates.
    
    Use this for:
    - Identifying training needs
    - Adjusting job requirements
    - Understanding candidate pool
    """
    try:
        skill_gaps = analytics_service.get_skill_gap_analysis(
            time_range=request.time_range,
            min_frequency=request.min_frequency,
            decision_filter=request.decision_filter
        )
        
        total_candidates = len(analytics_service.results)
        
        return SkillGapResponse(
            success=True,
            skill_gaps=skill_gaps,
            total_candidates_analyzed=total_candidates,
            time_range=request.time_range.value
        )
    
    except Exception as e:
        return SkillGapResponse(
            success=False,
            skill_gaps=[],
            total_candidates_analyzed=0,
            time_range=request.time_range.value,
            error=f"Skill analysis error: {str(e)}"
        )


@app.post(
    "/api/analytics/costs",
    response_model=CostResponse,
    tags=["Analytics"],
    summary="Analyze costs and spending"
)
async def analyze_costs(request: CostRequest):
    """
    Analyze costs and spending patterns.
    
    Returns:
    - Total spending
    - Cost per candidate
    - Phase breakdown
    - Projections (monthly/annual)
    
    Use this for:
    - Budget planning
    - Cost optimization
    - ROI calculations
    """
    try:
        cost_analysis = analytics_service.get_cost_analysis(request.time_range)
        
        return CostResponse(
            success=True,
            cost_analysis=cost_analysis,
            daily_costs=[]  # Can be populated with historical data
        )
    
    except Exception as e:
        return CostResponse(
            success=False,
            error=f"Cost analysis error: {str(e)}"
        )


# ============================================
# EXPORT ENDPOINTS (Phase 10)
# ============================================

@app.post(
    "/api/export",
    response_model=ExportResponse,
    tags=["Export"],
    summary="Export screening results"
)
async def export_results(request: ExportRequest):
    """
    Export screening results to CSV or JSON.
    
    Use this for:
    - Sharing results with team
    - Importing into ATS systems
    - Data backup
    - Reporting to stakeholders
    """
    try:
        # Get results to export
        results = analytics_service.results
        
        # Apply filters
        if request.decision_filter:
            results = [
                r for r in results
                if r.decision.upper() == request.decision_filter.upper()
            ]
        
        if request.min_score is not None:
            results = [r for r in results if r.overall_score >= request.min_score]
        
        if request.max_score is not None:
            results = [r for r in results if r.overall_score <= request.max_score]
        
        # Export based on format
        if request.format.value == "csv":
            data = analytics_service.export_to_csv(
                results,
                include_feedback=request.include_feedback,
                include_skills=request.include_skills
            )
            file_name = f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        elif request.format.value == "json":
            data = analytics_service.export_to_json(results)
            file_name = f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        else:
            return ExportResponse(
                success=False,
                total_records=0,
                format=request.format.value,
                error="Unsupported export format"
            )
        
        return ExportResponse(
            success=True,
            data=data,
            file_name=file_name,
            total_records=len(results),
            format=request.format.value
        )
    
    except Exception as e:
        return ExportResponse(
            success=False,
            total_records=0,
            format=request.format.value,
            error=f"Export error: {str(e)}"
        )


# ============================================
# FUTURE ENDPOINTS (Phase 11)
# ============================================
# 
# Phase 11: Production deployment, Docker, CI/CD, monitoring
# ============================================


if __name__ == "__main__":
    import uvicorn
    
    # WHY: This allows running the app with `python -m app.main`
    # Useful for debugging without uvicorn command
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug  # Auto-reload on code changes in dev mode
    )

