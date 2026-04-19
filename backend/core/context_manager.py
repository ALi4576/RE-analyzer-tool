"""
Context Injection module for PDF/document processing.
Enables ground truth verification against uploaded documents.
"""
from typing import Dict, List, Optional
import io
from utils import get_logger
from models.schemas import ContextInjectionPayload

logger = get_logger("context_manager")

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except (ImportError, KeyboardInterrupt):
    logger.warning("PyMuPDF (fitz) not available - PDF extraction disabled")
    FITZ_AVAILABLE = False


class ContextInjectionManager:
    """
    Manages context extraction and injection from PDF documents.
    This enables the AI agent to use uploaded PDFs as "Ground Truth"
    when analyzing user input.
    """
    
    def __init__(self):
        """Initialize context manager."""
        self.extracted_contexts: Dict[str, ContextInjectionPayload] = {}
        logger.info("Context Injection Manager initialized")
    
    def extract_pdf_content(self, pdf_path: str) -> ContextInjectionPayload:
        """
        Extract text content from PDF with structure preservation.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ContextInjectionPayload with extracted content
        """
        if not FITZ_AVAILABLE:
            logger.error("PyMuPDF not available - cannot extract PDF content")
            raise RuntimeError("PyMuPDF (fitz) is not installed. Please install it with: pip install PyMuPDF")
        
        try:
            logger.info(f"Extracting context from PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            
            # Extract metadata
            metadata = doc.metadata
            title = metadata.get("title", "Untitled Document")
            
            full_text = ""
            key_sections = {}
            
            # Process each page
            for page_num, page in enumerate(doc):
                text = page.get_text()
                full_text += text + "\n"
                
                # Try to identify sections by headers
                blocks = page.get_blocks()
                for block in blocks:
                    if block[1]:  # Has text
                        first_line = block[4].split('\n')[0].strip()
                        if len(first_line) > 5 and len(first_line) < 100:
                            key_sections[f"Section_{page_num}_{block[0]}"] = first_line
            
            doc.close()
            
            payload = ContextInjectionPayload(
                context_type="pdf",
                document_title=title,
                extracted_text=full_text.strip(),
                key_sections=key_sections,
            )
            
            self.extracted_contexts[pdf_path] = payload
            logger.info(f"PDF extraction complete: {len(full_text)} chars, {len(key_sections)} sections")
            
            return payload
            
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise
    
    def extract_txt_content(self, txt_path: str) -> ContextInjectionPayload:
        """
        Extract content from plain text file.
        
        Args:
            txt_path: Path to text file
            
        Returns:
            ContextInjectionPayload with extracted content
        """
        try:
            logger.info(f"Extracting context from TXT: {txt_path}")
            
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Identify key sections by paragraphs
            paragraphs = text.split('\n\n')
            key_sections = {}
            for idx, para in enumerate(paragraphs[:10]):  # First 10 sections
                if len(para) > 20:
                    section_title = para.split('\n')[0][:100]
                    key_sections[f"Section_{idx}"] = section_title
            
            payload = ContextInjectionPayload(
                context_type="text",
                document_title="Uploaded Document",
                extracted_text=text.strip(),
                key_sections=key_sections,
            )
            
            self.extracted_contexts[txt_path] = payload
            logger.info(f"TXT extraction complete: {len(text)} chars")
            
            return payload
            
        except Exception as e:
            logger.error(f"TXT extraction error: {str(e)}")
            raise
    
    def create_injection_prompt(
        self, user_input: str, context_payload: ContextInjectionPayload
    ) -> str:
        """
        Create an enhanced prompt with context injection.
        This is the key to ground truth verification.
        
        Args:
            user_input: User's spoken/typed requirements
            context_payload: Extracted context from PDF
            
        Returns:
            Enhanced prompt with context for the AI agent
        """
        logger.info("Creating context-injected prompt")
        
        section_text = "\n".join([
            f"- {k}: {v}" for k, v in context_payload.key_sections.items()
        ])
        
        injection_prompt = f"""
You are analyzing requirements in the context of a document.

GROUND TRUTH DOCUMENT:
Title: {context_payload.document_title}
Type: {context_payload.context_type}

Key Sections:
{section_text}

Full Document Context:
---
{context_payload.extracted_text[:3000]}  # First 3000 chars
---

USER INPUT (to be verified against context):
---
{user_input}
---

Your task is to:
1. Verify the user's input against the ground truth document
2. Flag any contradictions or inconsistencies
3. Identify gaps where the user didn't mention relevant document sections
4. Suggest clarifications needed
"""
        
        return injection_prompt.strip()
    
    def extract_and_cache(self, file_path: str) -> ContextInjectionPayload:
        """
        Smart extraction - detect file type and process accordingly.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted context payload
        """
        if file_path.lower().endswith('.pdf'):
            return self.extract_pdf_content(file_path)
        elif file_path.lower().endswith('.txt'):
            return self.extract_txt_content(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
    
    def get_cached_context(self, file_path: str) -> Optional[ContextInjectionPayload]:
        """Retrieve cached context without re-extraction."""
        return self.extracted_contexts.get(file_path)


# Global context manager instance
_context_manager = None


def get_context_manager() -> ContextInjectionManager:
    """Get or initialize the global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextInjectionManager()
    return _context_manager
