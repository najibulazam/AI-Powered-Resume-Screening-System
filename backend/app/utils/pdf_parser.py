"""
PDF Parsing Utilities

WHY THIS FILE EXISTS:
- Extract text from PDF files using PyMuPDF
- Provide deterministic, reliable parsing before AI processing
- Handle common PDF issues (encoding, formatting, corruption)

AGENTIC PRINCIPLE:
This is NOT an agent. This is infrastructure.
Agents consume the clean text output from these utilities.

Think of it as:
- Utility: "Convert PDF to text" (deterministic)
- Agent: "Understand what the text means" (AI-powered)
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ParsedDocument:
    """
    Result of parsing a document.
    
    WHY DATACLASS:
    - Simple data container (no complex methods)
    - Type hints for downstream consumers
    - Immutable by default (safer for parallel processing)
    """
    file_id: str
    filename: str
    raw_text: str  # Direct PDF extraction
    cleaned_text: str  # After normalization
    page_count: int
    char_count: int
    word_count: int
    is_valid: bool
    validation_errors: List[str]


class PDFParser:
    """
    Handles PDF text extraction and cleaning.
    
    WHY A CLASS:
    - Encapsulates PDF parsing logic
    - Can maintain state (page limits, error tolerance)
    - Easy to mock in tests
    """
    
    def __init__(self, min_chars: int = 100, max_pages: int = 20):
        """
        Initialize parser with validation thresholds.
        
        WHY THRESHOLDS:
        - min_chars: Reject empty/corrupt PDFs
        - max_pages: Prevent processing huge documents (cost control)
        """
        self.min_chars = min_chars
        self.max_pages = max_pages
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Dict[str, any]:
        """
        Extract raw text from PDF using PyMuPDF.
        
        WHY PYMUPDF:
        - Fast (C-based library)
        - Handles most PDF formats
        - Free and open source
        - Better than pdfplumber for plain text
        
        RETURNS: Dict with raw_text, page_count, success status
        """
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Check page count
            page_count = len(doc)
            if page_count > self.max_pages:
                return {
                    "success": False,
                    "error": f"PDF too long ({page_count} pages, max {self.max_pages})",
                    "raw_text": "",
                    "page_count": page_count
                }
            
            # Extract text from all pages
            raw_text = ""
            for page_num in range(page_count):
                page = doc[page_num]
                raw_text += page.get_text()
            
            doc.close()
            
            return {
                "success": True,
                "raw_text": raw_text,
                "page_count": page_count,
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse PDF: {str(e)}",
                "raw_text": "",
                "page_count": 0
            }
    
    def extract_text_from_txt(self, txt_path: Path) -> Dict[str, any]:
        """
        Read text from .txt files.
        
        WHY: Users might upload plain text instead of PDF.
        Unified interface: same output format as PDF extraction.
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            return {
                "success": True,
                "raw_text": raw_text,
                "page_count": 1,  # Text files = 1 "page"
                "error": None
            }
        
        except UnicodeDecodeError:
            # Try different encoding
            try:
                with open(txt_path, 'r', encoding='latin-1') as f:
                    raw_text = f.read()
                return {
                    "success": True,
                    "raw_text": raw_text,
                    "page_count": 1,
                    "error": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Encoding error: {str(e)}",
                    "raw_text": "",
                    "page_count": 0
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read text file: {str(e)}",
                "raw_text": "",
                "page_count": 0
            }
    
    def clean_text(self, raw_text: str) -> str:
        """
        Clean and normalize extracted text.
        
        WHY CLEANING:
        - PDFs have artifacts: headers, footers, page numbers
        - Extra whitespace from column layouts
        - Special characters from encoding issues
        
        WHAT WE DO:
        1. Remove excessive whitespace
        2. Fix line breaks (join hyphenated words)
        3. Remove non-printable characters
        4. Normalize unicode
        5. Remove common PDF artifacts
        """
        # Remove null bytes and control characters (except newline/tab)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', raw_text)
        
        # Normalize whitespace (but preserve paragraph breaks)
        text = re.sub(r' +', ' ', text)  # Multiple spaces → single space
        text = re.sub(r'\n\n+', '\n\n', text)  # Multiple newlines → double newline
        
        # Remove hyphenation at line breaks
        # "experi-\nence" → "experience"
        text = re.sub(r'-\s*\n\s*', '', text)
        
        # Fix common PDF artifacts
        text = text.replace('\uf0b7', '•')  # Bullet point
        text = text.replace('\u2022', '•')  # Another bullet
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '-')  # Em dash
        text = text.replace('\u2019', "'")  # Right single quote
        text = text.replace('\u201c', '"')  # Left double quote
        text = text.replace('\u201d', '"')  # Right double quote
        
        # Remove page numbers (common pattern: "Page 1 of 3" at top/bottom)
        text = re.sub(r'(?i)page\s+\d+\s*(?:of\s*\d+)?', '', text)
        
        # Remove excessive spacing
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        # Remove empty lines at start/end
        text = text.strip()
        
        return text
    
    def validate_text(self, text: str) -> tuple[bool, List[str]]:
        """
        Validate extracted text quality.
        
        WHY VALIDATION:
        - Detect corrupt/empty PDFs before sending to expensive LLM
        - Provide clear error messages to users
        - Prevent hallucinations from bad input
        
        RETURNS: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(text) < self.min_chars:
            errors.append(f"Text too short ({len(text)} chars, minimum {self.min_chars})")
        
        # Check if mostly gibberish (high ratio of non-alphabetic chars)
        alpha_chars = sum(c.isalpha() for c in text)
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars > 0:
            alpha_ratio = alpha_chars / total_chars
            if alpha_ratio < 0.5:  # Less than 50% letters
                errors.append(f"Text appears corrupted (only {alpha_ratio:.1%} alphabetic characters)")
        
        # Check if has some common resume/JD keywords
        # (Not AI - just basic sanity check)
        text_lower = text.lower()
        has_job_keywords = any(keyword in text_lower for keyword in [
            'experience', 'skill', 'education', 'work', 'position', 
            'role', 'responsibility', 'requirement', 'job', 'candidate'
        ])
        
        if not has_job_keywords:
            errors.append("Text doesn't contain common job/resume keywords (might be wrong document)")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def parse_document(
        self, 
        file_path: Path, 
        file_id: str, 
        filename: str
    ) -> ParsedDocument:
        """
        Main parsing pipeline: extract → clean → validate.
        
        WHY SINGLE METHOD:
        - One entry point for all document parsing
        - Consistent output format
        - Easier error handling
        
        USED BY: Agents will call this to get clean text
        """
        # Determine file type
        file_ext = file_path.suffix.lower()
        
        # Extract text
        if file_ext == '.pdf':
            result = self.extract_text_from_pdf(file_path)
        elif file_ext == '.txt':
            result = self.extract_text_from_txt(file_path)
        else:
            return ParsedDocument(
                file_id=file_id,
                filename=filename,
                raw_text="",
                cleaned_text="",
                page_count=0,
                char_count=0,
                word_count=0,
                is_valid=False,
                validation_errors=[f"Unsupported file type: {file_ext}"]
            )
        
        # Handle extraction failure
        if not result["success"]:
            return ParsedDocument(
                file_id=file_id,
                filename=filename,
                raw_text="",
                cleaned_text="",
                page_count=result["page_count"],
                char_count=0,
                word_count=0,
                is_valid=False,
                validation_errors=[result["error"]]
            )
        
        # Clean text
        raw_text = result["raw_text"]
        cleaned_text = self.clean_text(raw_text)
        
        # Validate
        is_valid, validation_errors = self.validate_text(cleaned_text)
        
        # Count words
        word_count = len(cleaned_text.split())
        
        return ParsedDocument(
            file_id=file_id,
            filename=filename,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            page_count=result["page_count"],
            char_count=len(cleaned_text),
            word_count=word_count,
            is_valid=is_valid,
            validation_errors=validation_errors
        )


# Singleton instance
pdf_parser = PDFParser()
