"""
File upload service for handling PDF, Audio, and document uploads.
Processes files asynchronously in background.
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import asyncio
from fastapi import UploadFile
from config import settings
from utils import get_logger
from core import get_transcriber, get_context_manager

logger = get_logger("file")


class FileUploadService:
    """
    Manages file uploads with async processing.
    
    Supported formats:
    - Audio: .wav, .mp3, .m4a, .ogg, .flac
    - Documents: .pdf, .txt, .docx
    """
    
    def __init__(self):
        """Initialize file upload service."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"File upload service initialized. Upload dir: {self.upload_dir}")
    
    async def save_upload(
        self, file: UploadFile, session_id: str
    ) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file object
            session_id: Session ID for organization
            
        Returns:
            Path to saved file
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Create session directory
            session_dir = self.upload_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = session_dir / file.filename
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            logger.info(f"File saved: {file_path} (size: {os.path.getsize(file_path)} bytes)")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            raise
    
    async def _validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file.
        
        Args:
            file: File to validate
            
        Raises:
            ValueError: If file is invalid
        """
        # Check filename
        if not file.filename:
            raise ValueError("Missing filename")
        
        # Extract extension
        ext = file.filename.split('.')[-1].lower()
        if ext not in settings.SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported: {', '.join(settings.SUPPORTED_FILE_TYPES)}"
            )
        
        # Check size
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file.size} bytes "
                f"(max: {settings.MAX_FILE_SIZE})"
            )
        
        logger.info(f"File validation passed: {file.filename}")
    
    async def process_audio_file(
        self, file_path: str, session_id: str, language: str = "en"
    ) -> str:
        """
        Process audio file: transcribe to text.
        
        Args:
            file_path: Path to audio file
            session_id: Session ID
            language: Language code
            
        Returns:
            Transcribed text
        """
        try:
            logger.info(f"Processing audio file: {file_path}")
            
            transcriber = get_transcriber()
            text = transcriber.transcribe_file(file_path, language)
            
            logger.info(f"Audio file processed. Transcription length: {len(text)}")
            
            return text
            
        except Exception as e:
            logger.error(f"Audio file processing error: {str(e)}")
            raise
    
    async def process_document_file(
        self, file_path: str, session_id: str
    ) -> str:
        """
        Process document file: extract and cache context.
        
        Args:
            file_path: Path to document file
            session_id: Session ID
            
        Returns:
            Extracted context text
        """
        try:
            logger.info(f"Processing document file: {file_path}")
            
            context_manager = get_context_manager()
            payload = context_manager.extract_and_cache(file_path)
            
            logger.info(f"Document processed. Extracted: {len(payload.extracted_text)} chars")
            
            return payload.extracted_text
            
        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            raise
    
    async def cleanup_session_files(self, session_id: str) -> None:
        """
        Clean up session upload files after export.
        
        Args:
            session_id: Session ID
        """
        try:
            session_dir = self.upload_dir / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up session files: {session_id}")
        
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")


# Global file service instance
_file_service = None


def get_file_service() -> FileUploadService:
    """Get or initialize the global file upload service."""
    global _file_service
    if _file_service is None:
        _file_service = FileUploadService()
    return _file_service
