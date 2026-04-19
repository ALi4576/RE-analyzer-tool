"""
Pydantic models and schemas for request/response handling.
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class RequirementSmell(str, Enum):
    """Types of requirement smells."""
    AMBIGUOUS = "ambiguous"
    INCOMPLETE = "incomplete"
    INFEASIBLE = "infeasible"
    CONFLICTING = "conflicting"
    UNMEASURABLE = "unmeasurable"
    VAGUE_SCOPE = "vague_scope"
    MISSING_RATIONALE = "missing_rationale"


class AnalysisStatus(str, Enum):
    """Status of requirement analysis."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    NEEDS_CLARIFICATION = "needs_clarification"
    CLARIFIED = "clarified"
    FORMAL_DRAFT = "formal_draft"
    COMPLETED = "completed"
    EXPORT_READY = "export_ready"


# ============ Request Models ============

class TranscribeAudioRequest(BaseModel):
    """Request to transcribe audio file."""
    file_path: str = Field(..., description="Path to audio file")
    language: Optional[str] = Field("en", description="Language code (ISO 639-1)")


class AnalyzeRequirementsRequest(BaseModel):
    """Request to analyze requirements text."""
    text: str = Field(..., description="Raw requirements text")
    context_file_path: Optional[str] = Field(None, description="Optional PDF path for context injection")
    session_id: str = Field(..., description="Session ID for tracking")


class ClarificationResponse(BaseModel):
    """User response to clarification question."""
    session_id: str = Field(..., description="Session ID")
    question_id: str = Field(..., description="ID of the question being answered")
    user_response: str = Field(..., description="User's clarification response")


class ExportRequirementRequest(BaseModel):
    """Request to export requirement to Jira/Trello."""
    session_id: str = Field(..., description="Session ID")
    export_target: str = Field(..., description="jira or trello")
    requirement_id: Optional[str] = Field(None, description="Specific requirement ID to export")


class StreamAudioRequest(BaseModel):
    """Initial WebSocket stream request."""
    session_id: str = Field(..., description="Session ID")
    context_file_path: Optional[str] = Field(None, description="Optional PDF for context injection")
    language: str = Field("en", description="Language code")


# ============ Response Models ============

class RequirementSmellAnalysis(BaseModel):
    """Analysis of requirement smells."""
    smell_type: RequirementSmell
    severity: float = Field(..., ge=0, le=1, description="Severity score 0-1")
    location: str = Field(..., description="Text location/excerpt")
    recommendation: str = Field(..., description="Recommended fix")


class ClarificationQuestion(BaseModel):
    """Question to ask user for clarification."""
    question_id: str = Field(..., description="Unique question ID")
    question: str = Field(..., description="The clarification question")
    context: Optional[str] = Field(None, description="Additional context")
    required_clarity: List[str] = Field(..., description="Aspects needing clarification")


class InterruptPayload(BaseModel):
    """WebSocket payload for interrupting analysis."""
    type: str = Field("interrupt", description="Message type")
    session_id: str = Field(..., description="Session ID")
    questions: List[ClarificationQuestion] = Field(..., description="List of clarification questions")
    analysis_state: Dict[str, Any] = Field(..., description="Current analysis state snapshot")


class ISORequirement(BaseModel):
    """ISO 29148 compliant requirement."""
    requirement_id: str = Field(..., description="Unique requirement ID")
    title: str = Field(..., description="Requirement title")
    shall_statement: str = Field(..., description="Formal 'shall' statement")
    rationale: str = Field(..., description="Business rationale")
    acceptance_criteria: List[str] = Field(..., description="Measurable acceptance criteria")
    priority: str = Field(..., description="High/Medium/Low")
    category: Optional[str] = Field(None, description="Functional/Non-functional/Interface")
    traceability: Optional[List[str]] = Field(None, description="Linked requirement IDs")


class AnalysisResponse(BaseModel):
    """Response from requirement analysis."""
    session_id: str = Field(..., description="Session ID")
    status: AnalysisStatus = Field(..., description="Current status")
    smells: List[RequirementSmellAnalysis] = Field(default_factory=list)
    smell_score: float = Field(..., ge=0, le=1, description="Overall smell score")
    logical_gap_score: float = Field(..., ge=0, le=1, description="Logical gap score")
    interrupt_needed: bool = Field(..., description="Whether human input is needed")
    clarification_questions: Optional[List[ClarificationQuestion]] = Field(None)
    original_text: str = Field(..., description="Original input text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FormalizedRequirement(BaseModel):
    """Final formalized requirement ready for export."""
    iso_requirements: List[ISORequirement] = Field(..., description="ISO 29148 formatted requirements")
    summary: str = Field(..., description="Executive summary")
    total_requirements: int = Field(..., description="Total number of requirements")
    completeness_score: float = Field(..., ge=0, le=1)
    ready_for_export: bool = Field(...)
    export_formats: List[str] = Field(..., description="Available export formats")


class ExportResult(BaseModel):
    """Result of exporting requirements."""
    export_id: str = Field(..., description="Export transaction ID")
    target: str = Field(..., description="jira or trello")
    ticket_ids: List[str] = Field(..., description="Created ticket IDs")
    status: str = Field(..., description="success or failed")
    url: Optional[str] = Field(None, description="Link to created resource")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContextInjectionPayload(BaseModel):
    """Context data injected from PDF."""
    context_type: str = Field("pdf", description="Document type")
    document_title: str = Field(..., description="Document title")
    extracted_text: str = Field(..., description="Extracted text content")
    key_sections: Dict[str, str] = Field(..., description="Important sections")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StreamChunk(BaseModel):
    """Audio chunk from WebSocket stream."""
    session_id: str = Field(..., description="Session ID")
    audio_data: bytes = Field(..., description="Raw PCM audio bytes")
    chunk_number: int = Field(..., description="Sequential chunk number")
    is_final: bool = Field(False, description="Whether this is final chunk")


# ============ State Models ============

class RequirementAnalysisState(BaseModel):
    """State model for LangGraph requirement analysis workflow."""
    session_id: str
    input_text: str
    context_docs: Optional[List[ContextInjectionPayload]] = None
    
    analysis_results: Optional[AnalysisResponse] = None
    user_clarifications: Optional[Dict[str, str]] = None
    
    requirements: List[ISORequirement] = Field(default_factory=list, description="Generated ISO requirements")
    formalized: Optional[FormalizedRequirement] = None
    export_results: Optional[List[ExportResult]] = None
    
    status: AnalysisStatus = AnalysisStatus.PENDING
    iteration_count: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
