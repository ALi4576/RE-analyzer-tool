"""
FastAPI routes for the RE Tool backend.
Exposes REST and WebSocket endpoints.
"""
import json
import re
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
import asyncio
from utils import get_logger
from models.schemas import (
    AnalyzeRequirementsRequest,
    ClarificationResponse,
    ClarifyRequest,
    ClarifyRequirementRequest,
    ExportRequirementRequest,
    PatchRequirementRequest,
    TranscribeAudioRequest,
    FormalizedRequirement,
    FormalizeRequest,
    ExportResult,
)
from core import (
    get_agent,
    get_transcriber,
    get_export_manager,
    get_formalizer,
)
from core.gpu_manager import get_gpu_manager
from services import (
    get_file_service,
    get_stream_service,
    get_reader_service,
    get_requirement_store,
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
    # Fast-reject inputs that are too short to be meaningful requirements
    if len(request.text.strip()) < 20:
        return {
            "session_id": request.session_id,
            "status": "pending",
            "interrupt_needed": False,
            "clarification_questions": None,
            "analysis_summary": {"smell_score": 0.0, "logical_gap_score": 0.0, "issues_found": 0},
        }

    try:
        # Gate concurrent LLM usage through the shared GPU semaphore
        gpu_manager = get_gpu_manager()
        async with gpu_manager.session_semaphore:
            logger.info(f"Starting analysis for session {request.session_id}")

            from models.schemas import RequirementAnalysisState

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

            # Run analysis (non-blocking — asyncio.to_thread inside agent.analyze)
            agent = get_agent()
            result = await agent.analyze(state)

            logger.info(f"Analysis complete for session {request.session_id}")

            # Coerce raw requirement dicts → validated fields with safe defaults
            raw_reqs = result.get("requirements", [])
            iso_requirements = []
            for i, req in enumerate(raw_reqs, 1):
                if not isinstance(req, dict):
                    continue
                iso_requirements.append({
                    "requirement_id": req.get("requirement_id") or f"REQ-{i:04d}",
                    "title": req.get("title") or "Untitled Requirement",
                    "shall_statement": req.get("shall_statement") or "The system shall meet this requirement.",
                    "rationale": req.get("rationale") or "",
                    "acceptance_criteria": req.get("acceptance_criteria") or [],
                    "priority": req.get("priority") or "Medium",
                    "category": req.get("category"),
                    "traceability": req.get("traceability") or req.get("depends_on") or [],
                    # Per-req completeness and smell-based quality so the
                    # frontend RequirementCard can render its own meter
                    # without a separate round-trip.
                    "completeness_score": req.get("completeness_score", 0.0),
                    "quality_score": req.get("quality_score", 1.0),
                })

            formalized_meta = result.get("formalized", {})

            return {
                "session_id": request.session_id,
                "status": result.get("status", "analyzing"),
                "interrupt_needed": result.get("interrupt_needed", False),
                "clarification_questions": result.get("clarification_questions"),
                "analysis_summary": {
                    "smell_score": result.get("smell_score"),
                    "logical_gap_score": result.get("logical_gap_score"),
                    "issues_found": len(result.get("smells", [])),
                },
                # Include requirements inline so the frontend needs only ONE call
                "iso_requirements": iso_requirements,
                "total_requirements": len(iso_requirements),
                "completeness_score": formalized_meta.get("completeness_score", 0.0),
                "quality_score": formalized_meta.get(
                    "quality_score",
                    formalized_meta.get("completeness_score", 0.0),
                ),
                "ready_for_export": formalized_meta.get("ready_for_export", False),
            }

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clarify")
async def clarify_requirements(request: ClarifyRequest):
    """
    Submit clarifications in response to analysis questions.
    Accepts {session_id, clarifications: {question_id: answer}} as sent by the frontend.
    """
    try:
        logger.info(f"Processing clarifications for session {request.session_id}")

        agent = get_agent()
        result = await agent.resume_after_clarification(request.session_id, request.clarifications)

        logger.info(f"Clarification processed for session {request.session_id}")

        # Include updated requirements in the response
        raw_reqs = result.get("requirements", [])
        iso_requirements = []
        for i, req in enumerate(raw_reqs, 1):
            if not isinstance(req, dict):
                continue
            iso_requirements.append({
                "requirement_id": req.get("requirement_id") or f"REQ-{i:04d}",
                "title": req.get("title") or "Untitled Requirement",
                "shall_statement": req.get("shall_statement") or "The system shall meet this requirement.",
                "rationale": req.get("rationale") or "",
                "acceptance_criteria": req.get("acceptance_criteria") or [],
                "priority": req.get("priority") or "Medium",
                "category": req.get("category"),
                "traceability": req.get("traceability") or req.get("depends_on") or [],
                "completeness_score": req.get("completeness_score", 0.0),
                "quality_score": req.get("quality_score", 1.0),
            })

        formalized_meta = result.get("formalized", {})
        return {
            "session_id": request.session_id,
            "status": result.get("status"),
            "interrupt_needed": result.get("interrupt_needed", False),
            "clarification_questions": result.get("clarification_questions"),
            "analysis_summary": {
                "smell_score": result.get("smell_score"),
                "logical_gap_score": result.get("logical_gap_score"),
                "issues_found": len(result.get("smells", [])),
            },
            "iso_requirements": iso_requirements,
            "total_requirements": len(iso_requirements),
            "completeness_score": formalized_meta.get("completeness_score", 0.0),
            "quality_score": formalized_meta.get(
                "quality_score",
                formalized_meta.get("completeness_score", 0.0),
            ),
            "ready_for_export": formalized_meta.get("ready_for_export", False),
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
async def formalize_requirements(request: FormalizeRequest):
    session_id = request.session_id
    try:
        logger.info(f"Retrieving requirements from memory for session {session_id}")

        agent = get_agent()
        config = {"configurable": {"thread_id": session_id}}
        state = agent.app.get_state(config)

        if not state.values:
            raise HTTPException(status_code=404, detail="No data found for this session ID")

        # Return partial data for in-progress sessions so the live panel can populate
        # incrementally; only hard-block on truly unknown/unstarted statuses.
        current_status = state.values.get("status", "")
        terminal_or_partial = ("formal_draft", "export_ready", "clarified", "analyzing", "needs_clarification")
        if current_status not in terminal_or_partial:
            raise HTTPException(
                status_code=409,
                detail=f"Analysis still in progress (status={current_status}). Retry after it completes."
            )

        raw_requirements = state.values.get("requirements", [])
        # Apply session overlay patches (user edits live outside the checkpointer).
        raw_requirements = get_requirement_store().merge(session_id, raw_requirements)

        # Coerce raw dicts → validated ISORequirement fields with safe defaults
        iso_requirements = []
        for i, req in enumerate(raw_requirements, 1):
            if not isinstance(req, dict):
                continue
            iso_requirements.append({
                "requirement_id": req.get("requirement_id") or f"REQ-{i:04d}",
                "title": req.get("title") or "Untitled Requirement",
                "shall_statement": req.get("shall_statement") or "The system shall meet this requirement.",
                "rationale": req.get("rationale") or "",
                "acceptance_criteria": req.get("acceptance_criteria") or [],
                "priority": req.get("priority") or "Medium",
                "category": req.get("category"),
                "traceability": req.get("traceability") or req.get("depends_on") or [],
                "completeness_score": req.get("completeness_score", 0.0),
                "quality_score": req.get("quality_score", 1.0),
            })

        formalized_meta = state.values.get("formalized", {})
        completeness = formalized_meta.get("completeness_score", 0.0)
        quality = formalized_meta.get("quality_score", completeness)

        # Do NOT mark a session export-ready while it is awaiting clarification —
        # otherwise the frontend would let the user export a draft built from
        # requirements that the pipeline flagged as needing human input.
        interrupt_needed = state.values.get("interrupt_needed", False)
        ready_for_export = len(iso_requirements) > 0 and not interrupt_needed

        return FormalizedRequirement(
            iso_requirements=iso_requirements,
            summary=f"Found {len(iso_requirements)} ISO 29148 requirements",
            total_requirements=len(iso_requirements),
            completeness_score=completeness,
            quality_score=quality,
            ready_for_export=ready_for_export,
            export_formats=["jira", "trello"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Formalization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Per-Requirement Edit Endpoints ============


def _find_requirement(requirements: list, requirement_id: str) -> Optional[dict]:
    """Locate a requirement dict by its requirement_id, or return None."""
    for req in requirements:
        if isinstance(req, dict) and req.get("requirement_id") == requirement_id:
            return req
    return None


def _coerce_iso_fields(req: dict, fallback_idx: int = 1) -> dict:
    """Normalize a requirement dict to the outward-facing ISO field shape."""
    return {
        "requirement_id": req.get("requirement_id") or f"REQ-{fallback_idx:04d}",
        "title": req.get("title") or "Untitled Requirement",
        "shall_statement": req.get("shall_statement") or "The system shall meet this requirement.",
        "rationale": req.get("rationale") or "",
        "acceptance_criteria": req.get("acceptance_criteria") or [],
        "priority": req.get("priority") or "Medium",
        "category": req.get("category"),
        "traceability": req.get("traceability") or req.get("depends_on") or [],
    }


@router.patch("/requirements/{session_id}/{requirement_id}")
async def patch_requirement(session_id: str, requirement_id: str, request: PatchRequirementRequest):
    """
    Apply a partial update to a single requirement within a session.

    Updates are stored in an overlay keyed by (session_id, requirement_id) and
    merged on every read path. The underlying LangGraph checkpoint is not
    mutated, so in-flight analyses cannot clobber user edits.
    """
    try:
        agent = get_agent()
        config = {"configurable": {"thread_id": session_id}}
        state = agent.app.get_state(config)

        if not state.values:
            raise HTTPException(status_code=404, detail="No data found for this session ID")

        store = get_requirement_store()
        patch_fields = request.dict(exclude_none=True)
        store.patch(session_id, requirement_id, patch_fields)

        raw_requirements = state.values.get("requirements", [])
        merged_requirements = store.merge(session_id, raw_requirements)

        updated = _find_requirement(merged_requirements, requirement_id)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Requirement '{requirement_id}' not found")

        # Find original positional index for stable fallback id generation.
        idx = 1
        for i, req in enumerate(merged_requirements, 1):
            if isinstance(req, dict) and req.get("requirement_id") == requirement_id:
                idx = i
                break

        return _coerce_iso_fields(updated, fallback_idx=idx)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Patch requirement error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _extract_json_object(text: str) -> dict:
    """
    Best-effort extraction of a JSON object from an LLM response.

    The analysis_llm is configured with ``format="json"`` so responses are
    already JSON, but models occasionally wrap output in prose or code fences.
    """
    if not text:
        raise ValueError("Empty LLM response")
    # Direct parse — the expected happy path under format="json".
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip triple-backtick fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return json.loads(fenced.group(1))
    # Last resort: grab the first top-level {...} block.
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))
    raise ValueError("No JSON object found in LLM response")


@router.post("/requirements/{session_id}/{requirement_id}/clarify")
async def clarify_requirement(session_id: str, requirement_id: str, request: ClarifyRequirementRequest):
    """
    Refine a single requirement by re-prompting the LLM with additional user context.

    The improved fields are stored in the overlay (never written back to the
    LangGraph checkpoint). If the LLM call or JSON parse fails, the store is
    left untouched and the endpoint returns 500.
    """
    try:
        agent = get_agent()
        config = {"configurable": {"thread_id": session_id}}
        state = agent.app.get_state(config)

        if not state.values:
            raise HTTPException(status_code=404, detail="No data found for this session ID")

        store = get_requirement_store()
        raw_requirements = state.values.get("requirements", [])
        merged_requirements = store.merge(session_id, raw_requirements)

        target = _find_requirement(merged_requirements, requirement_id)
        if target is None:
            raise HTTPException(status_code=404, detail=f"Requirement '{requirement_id}' not found")

        # Build the prompt. Send only the fields the LLM is meant to reason about.
        req_for_prompt = {
            "requirement_id": target.get("requirement_id"),
            "title": target.get("title"),
            "shall_statement": target.get("shall_statement"),
            "rationale": target.get("rationale"),
            "acceptance_criteria": target.get("acceptance_criteria") or [],
            "priority": target.get("priority"),
            "category": target.get("category"),
        }
        prompt = (
            "You are a requirements engineer. Improve the following ISO 29148 "
            "requirement using this additional context. Return ONLY a JSON object "
            "with these fields: title, shall_statement, rationale, "
            "acceptance_criteria (list), priority, category. "
            f"Requirement: {json.dumps(req_for_prompt, ensure_ascii=False)}. "
            f"Additional context: {request.additional_context}"
        )

        # agent.analysis_llm is the fast, JSON-formatted Ollama model (see agents.py:60-68).
        # Run the blocking model call off the event loop.
        try:
            llm_response = await asyncio.to_thread(agent.analysis_llm.invoke, prompt)
        except Exception as e:
            logger.error(f"Clarify LLM call failed for {requirement_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="LLM refinement failed")

        # LangChain LLMs may return str or an object with .content.
        text = llm_response if isinstance(llm_response, str) else getattr(llm_response, "content", str(llm_response))

        try:
            improved = _extract_json_object(text)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Clarify parse failed for {requirement_id}: {e}; raw={text!r}")
            raise HTTPException(status_code=500, detail="Failed to parse LLM response")

        # Whitelist the allowed overlay fields to keep the store honest.
        allowed_fields = {"title", "shall_statement", "rationale", "acceptance_criteria", "priority", "category"}
        patch_fields = {k: v for k, v in improved.items() if k in allowed_fields and v is not None}
        if not patch_fields:
            raise HTTPException(status_code=500, detail="LLM returned no usable fields")

        # Apply patch only after both call and parse succeeded.
        store.patch(session_id, requirement_id, patch_fields)

        # Re-merge so response reflects latest overlay.
        merged_requirements = store.merge(session_id, raw_requirements)
        updated = _find_requirement(merged_requirements, requirement_id)
        if updated is None:
            # Practically unreachable — we matched before patching.
            raise HTTPException(status_code=500, detail="Requirement disappeared after patch")

        idx = 1
        for i, req in enumerate(merged_requirements, 1):
            if isinstance(req, dict) and req.get("requirement_id") == requirement_id:
                idx = i
                break

        return {"iso_requirements": [_coerce_iso_fields(updated, fallback_idx=idx)]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clarify requirement error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============ Export Endpoints ============


@router.post("/export", response_model=ExportResult)
async def export_requirements(request: ExportRequirementRequest):
    try:
        logger.info(f"Exporting for session {request.session_id}")
        
        agent = get_agent()
        config = {"configurable": {"thread_id": request.session_id}}
        state = agent.app.get_state(config)
        raw_requirements = state.values.get("requirements", [])
        # Apply session overlay patches before building export payload.
        raw_requirements = get_requirement_store().merge(request.session_id, raw_requirements)

        if not raw_requirements:
            raise HTTPException(status_code=400, detail="No formalized requirements found to export.")

        # Coerce raw dicts → validated ISORequirement fields with safe defaults
        iso_requirements = []
        for i, req in enumerate(raw_requirements, 1):
            if not isinstance(req, dict):
                continue
            iso_requirements.append({
                "requirement_id": req.get("requirement_id") or f"REQ-{i:04d}",
                "title": req.get("title") or "Untitled Requirement",
                "shall_statement": req.get("shall_statement") or "The system shall meet this requirement.",
                "rationale": req.get("rationale") or "",
                "acceptance_criteria": req.get("acceptance_criteria") or [],
                "priority": req.get("priority") or "Medium",
                "category": req.get("category"),
                "traceability": req.get("traceability") or req.get("depends_on") or [],
            })

        formalized = FormalizedRequirement(
            iso_requirements=iso_requirements,
            summary=f"Exporting {len(iso_requirements)} requirements",
            total_requirements=len(iso_requirements),
            completeness_score=state.values.get("logical_gap_score", 0.0),
            ready_for_export=True,
            export_formats=["jira", "trello"],
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


@router.get("/export/pdf/{session_id}")
async def export_pdf(session_id: str):
    """Generate and download a PDF of the formalized requirements for a session."""
    try:
        from core.exporter import PdfExporter

        agent = get_agent()
        config = {"configurable": {"thread_id": session_id}}
        state = agent.app.get_state(config)
        raw_requirements = state.values.get("requirements", []) if state.values else []
        # Apply session overlay patches so the PDF reflects user edits.
        raw_requirements = get_requirement_store().merge(session_id, raw_requirements)

        if not raw_requirements:
            raise HTTPException(status_code=404, detail="No requirements found for this session.")

        pdf_path = await asyncio.to_thread(
            PdfExporter().export_requirements,
            raw_requirements,
            session_id,
        )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"requirements_{session_id[:12]}.pdf",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export error: {str(e)}", exc_info=True)
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
    - clarification_response: {type: "clarification_response", clarifications: {q_id: answer}}
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
