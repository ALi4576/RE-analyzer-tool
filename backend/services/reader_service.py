"""
PDF/Document reader service for static file processing.
Separate from stream service for file-based uploads.
"""
from typing import Dict, Optional
from pathlib import Path
from utils import get_logger
from core import get_context_manager
from models.schemas import ContextInjectionPayload

logger = get_logger("file")


class DocumentReaderService:
    """
    Read and process static documents (PDF, TXT, DOCX).
    Returns structured context for injection into AI analysis.
    """
    
    def __init__(self):
        """Initialize document reader service."""
        self.context_manager = get_context_manager()
        logger.info("Document Reader Service initialized")
    
    async def read_document(
        self, file_path: str
    ) -> ContextInjectionPayload:
        """
        Read document and extract context.
        
        Args:
            file_path: Path to document
            
        Returns:
            Extracted context payload
        """
        try:
            logger.info(f"Reading document: {file_path}")
            
            # Check if already cached
            cached = self.context_manager.get_cached_context(file_path)
            if cached:
                logger.info(f"Using cached context for {file_path}")
                return cached
            
            # Extract new context
            payload = self.context_manager.extract_and_cache(file_path)
            logger.info(f"Document read and cached: {len(payload.extracted_text)} chars")
            
            return payload
            
        except Exception as e:
            logger.error(f"Document read error: {str(e)}")
            raise
    
    async def get_document_summary(
        self, file_path: str
    ) -> Dict[str, str]:
        """
        Get a summary of document content.
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with title and key sections
        """
        try:
            payload = await self.read_document(file_path)
            
            summary = {
                "title": payload.document_title,
                "type": payload.context_type,
                "text_length": len(payload.extracted_text),
                "section_count": len(payload.key_sections),
                "sections": list(payload.key_sections.values())[:5],  # First 5
            }
            
            logger.info(f"Document summary created for {file_path}")
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            raise


# Global reader service instance
_reader_service = None


def get_reader_service() -> DocumentReaderService:
    """Get or initialize the global document reader service."""
    global _reader_service
    if _reader_service is None:
        _reader_service = DocumentReaderService()
    return _reader_service
