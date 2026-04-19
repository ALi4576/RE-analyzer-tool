"""
WebSocket handler for real-time stream processing and Human-in-the-Loop.
Manages bidirectional communication with frontend.

FIXED VERSION: Properly handles state, streaming, and LangGraph integration.
"""
import json
import asyncio
import uuid
import base64
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from config import settings
from utils import get_logger
from models.schemas import (
    RequirementAnalysisState,
    AnalysisStatus,
)
from core import get_agent, get_transcriber
from core.gpu_manager import get_gpu_manager
from core.session_manager import get_session_manager
from services import get_reader_service

logger = get_logger("agent")


class WebSocketManager:
    """Manages WebSocket connections and lifecycle."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
        logger.info("WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Register new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")

    async def disconnect(self, session_id: str) -> None:
        """Cleanup disconnected WebSocket."""
        async with self._lock:
            self.active_connections.pop(session_id, None)
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_message(self, session_id: str, message: Dict) -> bool:
        """
        Send message to client.
        
        Args:
            session_id: Session ID
            message: Message dict (will be JSON encoded)
            
        Returns:
            True if sent successfully
        """
        try:
            if session_id not in self.active_connections:
                logger.warning(f"No active connection for session {session_id}")
                return False
            
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
            logger.debug(f"Message sent to {session_id}: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    async def receive_message(self, session_id: str) -> Optional[Dict]:
        """
        Receive message from client.
        
        Args:
            session_id: Session ID
        
        Returns:
            Decoded message dict (None if error)
        """
        try:
            if session_id not in self.active_connections:
                logger.warning(f"No active connection for session {session_id}")
                return None
            
            websocket = self.active_connections[session_id]
            message = await websocket.receive_json()
            logger.debug(f"Message received from {session_id}: {message.get('type', 'unknown')}")
            return message
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected for session {session_id}")
            await self.disconnect(session_id)
        except Exception as e:
            logger.error(f"Failed to receive message: {str(e)}")
        return None


class StreamingAnalysisHandler:
    """
    Handles real-time audio streaming and analysis.
    
    FIXED: Uses proper state handshake, session persistence, and LangGraph integration.
    """
    
    def __init__(self):
        """Initialize handler."""
        self.ws_manager = WebSocketManager()
        self.reader_service = get_reader_service()
        self.agent = get_agent()
        self.transcriber = get_transcriber()
        self.gpu_manager = get_gpu_manager()
        self.session_manager = get_session_manager()
        logger.info("Streaming Analysis Handler initialized")
    
    async def handle_stream(self, websocket: WebSocket, session_id: str, context_file: Optional[str] = None):
        """
        Handle real-time audio stream for a session.
        
        Args:
            websocket: WebSocket connection instance
            session_id: Session ID for tracking
            context_file: Optional context file path for context injection
        """
        await self.ws_manager.connect(websocket, session_id)
        
        # Acquire GPU slot
        gpu_acquired = await self.gpu_manager.acquire_session_slot(session_id)
        if not gpu_acquired:
            await self.ws_manager.send_message(
                session_id,
                {"type": "error", "message": "GPU resource unavailable - max concurrent sessions reached"},
            )
            await self.ws_manager.disconnect(session_id)
            return
        
        # Create session
        self.session_manager.create_session(session_id, context_file)
        
        try:
            # Load context if provided
            context_docs = []
            if context_file:
                try:
                    context_payload = await self.reader_service.read_document(context_file)
                    context_docs = [context_payload]
                    logger.info(f"Context loaded for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to load context: {str(e)}")
            
            # Accumulate transcribed text
            accumulated_text = ""
            chunk_count = 0
            
            while True:
                message = await self.ws_manager.receive_message(session_id)
                if not message:
                    break
                
                msg_type = message.get("type")
                
                if msg_type == "audio_chunk":
                    accumulated_text = await self._handle_audio_chunk(session_id, message, context_docs, accumulated_text)
                    chunk_count += 1
                    
                elif msg_type == "finalize":
                    logger.info(f"Finalizing stream for session {session_id}")
                    break
                    
                elif msg_type == "clarification_response":
                    await self._handle_clarification(session_id, message)
        
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"Stream handling error for session {session_id}: {str(e)}", exc_info=True)
        finally:
            # Cleanup
            self.session_manager.end_session(session_id)
            self.gpu_manager.release_session_slot(session_id)
            self.gpu_manager.clear_cache()  # Clear GPU cache after session
            await self.ws_manager.disconnect(session_id)
            logger.info(f"GPU stats: {self.gpu_manager.get_stats()}")
    
    async def _handle_audio_chunk(
        self, session_id: str, message: Dict, context_docs: List, accumulated_text: str
    ) -> str:
        """
        Handle incoming audio chunk.

        Returns the updated accumulated_text so the caller can persist it;
        Python strings are immutable so parameter mutation would be a no-op.

        Args:
            session_id: Session ID
            message: Message containing audio data
            context_docs: Context documents
            accumulated_text: Current accumulated text

        Returns:
            Updated accumulated text (original + new transcription)
        """
        try:
            chunk_data = message.get("data")
            chunk_number = message.get("chunk_number", 0)

            # Decode base64 audio if needed
            if isinstance(chunk_data, str):
                audio_bytes = base64.b64decode(chunk_data)
            else:
                audio_bytes = chunk_data

            # Transcribe audio chunk
            transcription = self.transcriber.transcribe_stream(audio_bytes, chunk_number)

            if transcription:
                accumulated_text = accumulated_text + " " + transcription

            # Send chunk acknowledgment
            await self.ws_manager.send_message(
                session_id,
                {
                    "type": "chunk_ack",
                    "chunk_number": chunk_number,
                    "transcription": transcription or "",
                    "accumulated_length": len(accumulated_text),
                },
            )

            # Trigger analysis every 50 characters (sliding window)
            if len(accumulated_text) > 0 and len(accumulated_text) % 50 == 0:
                logger.info(f"Triggering incremental analysis for session {session_id} at {len(accumulated_text)} chars")
                await self._run_analysis(session_id, accumulated_text, context_docs)

        except Exception as e:
            logger.error(f"Audio chunk handling error: {str(e)}")
            await self.ws_manager.send_message(
                session_id,
                {"type": "error", "message": f"Audio chunk error: {str(e)}"},
            )

        return accumulated_text
    
    async def _run_analysis(self, session_id: str, text: str, context_docs: List):
        """Run analysis on accumulated text."""
        try:
            state = RequirementAnalysisState(
                session_id=session_id,
                input_text=text.strip(),
                context_docs=context_docs if context_docs else None,
            )
            
            result = await self.agent.analyze(state)
            
            # SCRIBE MODE: Always include requirements_list (never null)
            requirements_list = result.get("requirements", [])
            formalized_data = result.get("formalized", {})
            completeness_score = formalized_data.get("completeness_score", 0)
            
            # Send analysis update with MANDATORY requirements_list field
            await self.ws_manager.send_message(
                session_id,
                {
                    "type": "analysis_update",
                    "status": result.get("status", "analyzing"),
                    "interrupt_needed": result.get("interrupt_needed", False),
                    
                    # MANDATORY FIELDS (SCRIBE MODE):
                    "requirements_list": requirements_list,  # NEVER NULL
                    "requirements_count": len(requirements_list),
                    "completeness_score": completeness_score,
                    
                    # SCORING INFO (SECONDARY):
                    "analysis_summary": {
                        "smell_score": result.get("smell_score", 0),
                        "logical_gap_score": result.get("logical_gap_score", 0),
                        "issues_found": len(result.get("smells", [])) if result.get("smells") else 0,
                    },
                    
                    # CLARIFICATION IF NEEDED:
                    "clarification_questions": result.get("clarification_questions") or None,
                    "formalized": formalized_data,
                },
            )
            
            # If interruption needed, send clarification questions
            if result.get("interrupt_needed") and result.get("clarification_questions"):
                await self.ws_manager.send_message(
                    session_id,
                    {
                        "type": "interrupt",
                        "clarification_questions": result.get("clarification_questions", []),
                        "requirements_list": requirements_list,  # Include in interrupt too
                        "requirements_count": len(requirements_list),
                    },
                )
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
    
    async def _handle_clarification(self, session_id: str, message: Dict):
        """Handle user clarification response."""
        try:
            clarifications = message.get("clarifications", {})
            logger.info(f"Processing clarifications for session {session_id}")
            
            result = await self.agent.resume_after_clarification(session_id, clarifications)
            
            # SCRIBE MODE: Always include requirements_list
            requirements_list = result.get("requirements", [])
            formalized_data = result.get("formalized", {})
            completeness_score = formalized_data.get("completeness_score", 0)
            
            await self.ws_manager.send_message(
                session_id,
                {
                    "type": "clarification_processed",
                    "status": result.get("status"),
                    
                    # MANDATORY FIELDS (SCRIBE MODE):
                    "requirements_list": requirements_list,  # NEVER NULL
                    "requirements_count": len(requirements_list),
                    "completeness_score": completeness_score,
                    
                    # SCORING INFO:
                    "analysis_summary": {
                        "smell_score": result.get("smell_score", 0),
                        "logical_gap_score": result.get("logical_gap_score", 0),
                        "issues_found": len(result.get("smells", [])) if result.get("smells") else 0,
                    },
                    
                    "formalized": formalized_data,
                },
            )
        except Exception as e:
            logger.error(f"Clarification processing error: {str(e)}")
            await self.ws_manager.send_message(
                session_id,
                {"type": "error", "message": f"Clarification error: {str(e)}"},
            )


# Global handler instance
_handler = None


def get_streaming_handler() -> StreamingAnalysisHandler:
    """Get or initialize global streaming handler."""
    global _handler
    if _handler is None:
        _handler = StreamingAnalysisHandler()
    return _handler
