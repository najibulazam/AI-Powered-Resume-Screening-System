"""
File Upload Utilities

WHY THIS FILE:
- Handle file I/O operations (save, validate, cleanup)
- Keep main.py clean (no file handling logic in endpoints)
- Reusable across different upload types

AGENTIC PRINCIPLE:
Utilities are "dumb infrastructure". They don't make decisions,
they just execute tasks. Agents will use these utilities but
the intelligence stays in the agents.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from datetime import datetime

from app.config import get_settings
from app.schemas.upload import FileMetadata

settings = get_settings()


class FileHandler:
    """
    Handles all file operations for uploads.
    
    WHY A CLASS:
    - Encapsulates file logic (easier to test)
    - Can be mocked in unit tests
    - Maintains consistent file naming conventions
    """
    
    def __init__(self):
        """
        Initialize upload directories.
        
        WHY: Create folders if they don't exist (prevents crashes on first run)
        """
        self.base_upload_dir = Path(settings.upload_dir)
        self.job_desc_dir = self.base_upload_dir / "job_descriptions"
        self.resume_dir = self.base_upload_dir / "resumes"
        
        # Create directories
        self.job_desc_dir.mkdir(parents=True, exist_ok=True)
        self.resume_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_id(self, prefix: str) -> str:
        """
        Generate unique file ID.
        
        WHY: Prevents filename collisions (two users upload "resume.pdf")
        FORMAT: jd_20231226_abc123 or resume_20231226_xyz789
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}"
    
    def _validate_file(self, file: UploadFile, max_size_mb: int = 10) -> None:
        """
        Validate uploaded file.
        
        WHY: Security & cost control
        - Prevent huge files (DOS attack or innocent mistakes)
        - Only allow PDFs (prevents malicious executables)
        
        RAISES: HTTPException if validation fails
        """
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        allowed_extensions = {".pdf", ".txt"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (read file to get size)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()  # Get position (file size)
        file.file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size_mb}MB"
            )
    
    async def save_job_description(self, file: UploadFile) -> FileMetadata:
        """
        Save job description file.
        
        WHY ASYNC: File I/O can block the event loop.
        Using async allows handling multiple uploads concurrently.
        
        RETURNS: FileMetadata with file location and ID
        """
        # Validate first
        self._validate_file(file, max_size_mb=settings.max_file_size_mb)
        
        # Generate unique ID
        file_id = self._generate_file_id("jd")
        
        # Preserve original extension
        file_ext = Path(file.filename).suffix
        new_filename = f"{file_id}{file_ext}"
        file_path = self.job_desc_dir / new_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        finally:
            file.file.close()
        
        # Get file size
        file_size = file_path.stat().st_size
        
        return FileMetadata(
            file_id=file_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type="job_description",
            file_size=file_size
        )
    
    async def save_resumes(self, files: List[UploadFile]) -> List[FileMetadata]:
        """
        Save multiple resume files.
        
        WHY SEPARATE FROM JOB DESC:
        - Different folder (organization)
        - Different ID prefix (easier to identify)
        - Batch validation (fail fast if any file invalid)
        
        RETURNS: List of FileMetadata for each successfully saved file
        """
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Validate all files first (fail fast)
        for file in files:
            self._validate_file(file, max_size_mb=settings.max_file_size_mb)
        
        metadata_list = []
        
        for file in files:
            # Generate unique ID for each resume
            file_id = self._generate_file_id("resume")
            
            # Preserve original extension
            file_ext = Path(file.filename).suffix
            new_filename = f"{file_id}{file_ext}"
            file_path = self.resume_dir / new_filename
            
            # Save file
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as e:
                # Cleanup already saved files on error
                for metadata in metadata_list:
                    Path(metadata.file_path).unlink(missing_ok=True)
                
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save {file.filename}: {str(e)}"
                )
            finally:
                file.file.close()
            
            # Get file size
            file_size = file_path.stat().st_size
            
            metadata_list.append(
                FileMetadata(
                    file_id=file_id,
                    filename=file.filename,
                    file_path=str(file_path),
                    file_type="resume",
                    file_size=file_size
                )
            )
        
        return metadata_list
    
    def list_files(self) -> List[FileMetadata]:
        """
        List all uploaded files.
        
        WHY: Needed for testing and orchestration to find available files.
        Scans both job_descriptions and resumes directories.
        
        RETURNS: List of FileMetadata for all uploaded files
        """
        metadata_list = []
        
        # List job descriptions
        for file_path in self.job_desc_dir.glob("*"):
            if file_path.is_file():
                # Extract file_id (prefix before first underscore group)
                parts = file_path.stem.split("_")
                file_id = f"{parts[0]}_{parts[1]}_{parts[2]}" if len(parts) >= 3 else file_path.stem
                
                metadata_list.append(
                    FileMetadata(
                        file_id=file_id,
                        filename=file_path.name,
                        file_path=str(file_path),
                        file_type="job_description",
                        file_size=file_path.stat().st_size
                    )
                )
        
        # List resumes
        for file_path in self.resume_dir.glob("*"):
            if file_path.is_file():
                # Extract file_id
                parts = file_path.stem.split("_")
                file_id = f"{parts[0]}_{parts[1]}_{parts[2]}" if len(parts) >= 3 else file_path.stem
                
                metadata_list.append(
                    FileMetadata(
                        file_id=file_id,
                        filename=file_path.name,
                        file_path=str(file_path),
                        file_type="resume",
                        file_size=file_path.stat().st_size
                    )
                )
        
        return metadata_list
    
    def get_file_path(self, file_id: str, file_type: str) -> Path:
        """
        Get file path from file ID.
        
        WHY: Agents need to read files by ID, not by path.
        This abstracts away the storage location.
        """
        if file_type == "job_description":
            search_dir = self.job_desc_dir
        elif file_type == "resume":
            search_dir = self.resume_dir
        else:
            raise ValueError(f"Invalid file_type: {file_type}")
        
        # Find file with matching ID prefix
        for file_path in search_dir.glob(f"{file_id}*"):
            return file_path
        
        raise FileNotFoundError(f"File not found: {file_id}")
    
    def cleanup_temp_files(self, file_ids: List[str]) -> None:
        """
        Delete temporary files after processing.
        
        WHY: Free up disk space after agents finish processing.
        In production, you'd move to S3/cloud storage instead of deleting.
        """
        for file_id in file_ids:
            for file_type in ["job_description", "resume"]:
                try:
                    file_path = self.get_file_path(file_id, file_type)
                    file_path.unlink(missing_ok=True)
                except FileNotFoundError:
                    continue  # Already deleted or never existed


# Singleton instance
file_handler = FileHandler()
