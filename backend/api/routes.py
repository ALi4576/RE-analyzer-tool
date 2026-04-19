"""
FastAPI routes for the RE Tool backend.
Exposes REST and WebSocket endpoints.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio
from utils import get_logger
from models.schemas import (
    AnalyzeRequirementsRequest,
    ClarificationResponse,
    ExportRequirementRequest,
    TranscribeAudioRequest,
    FormalizedRequirement,
    ExportResult,
)
from core import (
    get_agent,
    get_transcriber,
    get_export_manager,
    get_formalizer,
)
from services import (
    get_file_service,
    get_stream_service,
    get_reader_service,
)
from api.websocket_handler import get_streaming_handler

logger = get_logger("agent")
router = APIRouter()


# ============ Analysis Endpoints ============

@router.post("/analyze")
async def analyze_requirements(request: AnalyzeRequirementsRequest):
    """
    Analyze raw requirements text.
    Runs the full pipeline: parsing -> smell detection -> formalization.

    The analysis may be interrupted if quality issues are found,
    requesting human clarification via returned questions.
    """
    try:
        logger.info(f"Starting analysis for session {request.session_id}")

        from models.schemas import RequirementAnalysisState, AnalysisStatus

        # Create analysis state
        state = RequirementAnalysisState(
            session_id=request.session_id,
            input_text=request.text,
        )

        # Load context if provided
        if request.context_file_path:
            logger.info(f"Loading context from {request.context_file_path}")
            reader_service = get_reader_service()
            try:
                context_payload = await reader_service.read_document(request.context_file_path)
                state.context_docs = [context_payload]
                logger.info("Context loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load context: {str(e)}")

        # Run analysis
        agent = get_agent()
        result = agent.analyze(state)

        logger.info(f"Analysis complete for session {request.session_id}")

        return {
            "session_id": request.session_id,
            "status": result.get("status", "analyzing"),
            "interrupt_needed": result.get("interrupt_needed", False),
            "clarification_questions": result.get("clarification_questions"),
            "analysis_summary": {
                "smell_score": result.get("smell_score"),
                "logical_gap_score": result.get("logical_gap_score"),
                "issues_found": len(result.get("smells", [])),
            }
        }

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clarify")
async def clarify_requirements(response: ClarificationResponse):
    """
    Submit clarifications in response to analysis questions.
    Resumes the analysis workflow with user's answers.
    """
    try:
        logger.info(
            f"Processing clarifications for session {response.session_id}")

        agent = get_agent()
        clarifications = {response.question_id: response.user_response}

        result = agent.resume_after_clarification(
            response.session_id,
            clarifications
        )

        logger.info(
            f"Clarification processed for session {response.session_id}")

        return {
            "session_id": response.session_id,
            "status": result.get("status"),
            "interrupt_needed": result.get("interrupt_needed", False),
        }

    except Exception as e:
        logger.error(f"Clarification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Transcription Endpoints ============

@router.post("/transcribe")
async def transcribe_audio(request: TranscribeAudioRequest):
    """
    Transcribe an audio file to text.
    
    Args:
        request: TranscribeAudioRequest
    
    Returns:
        Transcribed text
    """
    try:
        transcriber = get_transcriber()
        transcription = transcriber.transcribe_file(
            file_path=request.file_path, language=request.language
        )
        return {"transcription": transcription}
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Transcription failed")


# ============ File Upload Endpoints ============

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload and transcribe audio file.

    Returns:
        - file_path: Where file is stored
        - transcription: Transcribed text
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(
            f"Uploading audio file: {file.filename} (session: {session_id})")

        file_service = get_file_service()
        file_path = await file_service.save_upload(file, session_id)

        # Transcribe
        text = await file_service.process_audio_file(file_path, session_id)

        logger.info(f"Audio uploaded and transcribed: {len(text)} chars")

        return {
            "session_id": session_id,
            "file_path": file_path,
            "filename": file.filename,
            "transcription": text,
            "text_length": len(text),
        }

    except Exception as e:
        logger.error(f"Audio upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload document for context injection.
    Supported: .pdf, .txt

    Returns:
        - context: Extracted document context
        - sections: Key document sections
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(
            f"Uploading document: {file.filename} (session: {session_id})")

        file_service = get_file_service()
        file_path = await file_service.save_upload(file, session_id)

        # Extract context
        reader_service = get_reader_service()
        summary = await reader_service.get_document_summary(file_path)

        logger.info(f"Document uploaded: {summary}")

        return {
            "session_id": session_id,
            "file_path": file_path,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============ Formalization Endpoints ============

@router.post("/formalize", response_model=FormalizedRequirement)
async def formalize_requirements(session_id: str):
    try:
        logger.info(
            f"Retrieving requirements from memory for session {session_id}")

        agent = get_agent()

        # 1. Reach into the LangGraph Memory (The 'Database' in RAM)
        config = {"configurable": {"thread_id": session_id}}
        state = agent.app.get_state(config)

        # 2. Check if the AI actually has data for this session
        if not state.values:
            raise HTTPException(
                status_code=404, detail="No data found for this session ID")

        # 3. Pull the actual requirements found by the AI nodes
        # Note: 'requirements' must match the key used in your AgentState TypedDict
        ai_requirements = state.values.get("requirements", [])

        # 4. Return the ACTUAL data to your Flutter/React app
        return FormalizedRequirement(
            iso_requirements=ai_requirements,
            summary=f"Found {len(ai_requirements)} requirements",
            total_requirements=len(ai_requirements),
            completeness_score=state.values.get("logical_gap_score", 0.0),
            ready_for_export=len(ai_requirements) > 0,
            export_formats=["jira", "trello"]
        )

    except Exception as e:
        logger.error(f"Formalization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Export Endpoints ============


@router.post("/export", response_model=ExportResult)
async def export_requirements(request: ExportRequirementRequest):
    try:
        logger.info(f"Exporting for session {request.session_id}")
        
        agent = get_agent()
        # 1. Pull actual requirements from AI memory
        config = {"configurable": {"thread_id": request.session_id}}
        state = agent.app.get_state(config)
        ai_requirements = state.values.get("requirements", [])

        if not ai_requirements:
            raise HTTPException(status_code=400, detail="No formalized requirements found to export.")

        # 2. Package them for the export manager
        formalized = FormalizedRequirement(
            iso_requirements=ai_requirements,
            summary=f"Exporting {len(ai_requirements)} requirements",
            total_requirements=len(ai_requirements),
            completeness_score=state.values.get("logical_gap_score", 0.0),
            ready_for_export=True,
            export_formats=["jira", "trello"]
        )

        export_manager = get_export_manager()
        result = export_manager.export(formalized, request.export_target)
        
        return result

    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/dry-run")
async def export_dry_run(request: ExportRequirementRequest):
    """
    Preview what would be exported without creating tickets.
    """
    try:
        logger.info(
            f"Performing dry-run export for session {request.session_id}")

        export_manager = get_export_manager()

        formalized = FormalizedRequirement(
            iso_requirements=[],
            summary="Export demonstration",
            total_requirements=0,
            completeness_score=0.0,
            ready_for_export=False,
            export_formats=["jira", "trello"],
        )

        preview = export_manager.dry_run(formalized, request.export_target)

        return {
            "session_id": request.session_id,
            "preview": preview,
        }

    except Exception as e:
        logger.error(f"Dry-run error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Health & Status Endpoints ============

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "transcriber": "ready",
            "agent": "ready",
            "exporter": "ready",
        }
    }


@router.get("/status")
async def get_status():
    """Get system status and capabilities."""
    return {
        "system": "Multi-Agentic RE Tool Backend",
        "version": "0.1.0",
        "features": {
            "audio_streaming": True,
            "file_upload": True,
            "real_time_analysis": True,
            "human_in_loop": True,
            "jira_export": True,
            "trello_export": True,
        },
        "requirements": {
            "gpu": "RTX 4070 Super (CUDA)",
            "models": ["Faster-Whisper (base)", "Ollama Llama 3"],
        }
    }


# ============ WebSocket Endpoints ============

@router.websocket("/ws/stream/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str, context_file: Optional[str] = None):
    """
    WebSocket endpoint for real-time audio streaming and analysis.

    Handles:
    - Real-time audio chunk streaming (binary)
    - Automatic transcription
    - Continuous analysis
    - Human-in-the-loop interrupts
    - Clarification Q&A

    Message Protocol:

    Client -> Server:
    - audio_chunk: {type: "audio_chunk", data: base64_audio, chunk_number: N}
    - clarification_response: {type: "clarification_response", questions: {q_id: answer}}
    - finalize: {type: "finalize"}
    - status: {type: "status"}

    Server -> Client:
    - connection_ready: Session connected
    - chunk_ack: Audio chunk acknowledged
    - transcription: New transcription available
    - interrupt: HITL - requires clarification
    - analysis_complete: Analysis finished
    - error: Error occurred
    """
    try:
        handler = get_streaming_handler()
        await handler.handle_stream(websocket, session_id, context_file)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
