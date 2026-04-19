"""
Main FastAPI application for Multi-Agentic Requirements Engineering Tool.

Architecture Overview:
=======================

1. INFERENCE LAYER (GPU via RTX 4070 Super)
   - Ollama LLM Server (Llama 3): Requirement analysis & formalization
   - Faster-Whisper: Real-time audio transcription
   
2. ORCHESTRATION LAYER (LangGraph)
   - StatefulGraph: Tracks requirement journey
   - Interrupt Pattern: Human-in-the-Loop (HITL)
   - State Checkpointing: Pause/Resume workflows
   
3. DATA INGESTION LAYER
   - Audio Stream Service: WebSocket PCM → Whisper → Text
   - File Service: PDF/DOC upload → Context extraction
   - Reader Service: Context injection for ground truth verification
   
4. ANALYSIS LAYER (Multi-Agent Squad)
   - Parser Agent: Entity extraction & normalization
   - Smell Detector: Quality issue identification
   - Logic Analyzer: Gap & conflict detection
   - Clarifier: Question generation
   - Formalizer: ISO 29148 compliance
   
5. EXPORT LAYER
   - Jira Exporter: Create stories & requirements
   - Trello Exporter: Create/organize cards
   - PDF Generator: Formal spec documents
   
6. COMMUNICATION LAYER
   - FastAPI REST: Traditional request/response
   - WebSocket: Real-time streaming & HITL
   - JSON: Structured data exchange

Key Design Patterns:
====================
- Async/Await: Non-blocking I/O for GPU operations
- Context Injection: PDF as ground truth for verification
- HITL Workflow: Automatic interruption on quality issues
- State Persistence: LangGraph checkpoint system
- Singleton Pattern: Shared GPU-bound resources
"""

import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from utils import get_logger
from api import router

# Setup logging
logger = get_logger("main")


# ============ Lifecycle Events ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    Initializes GPU-bound resources on startup.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Multi-Agentic RE Tool Backend Starting")
    logger.info("=" * 60)
    logger.info(f"GPU: RTX 4070 Super")
    logger.info(f"Ollama Model: {settings.OLLAMA_MODEL}")
    logger.info(f"Whisper Model: {settings.WHISPER_MODEL_SIZE}")
    logger.info(f"CORS Origins: *")
    
    # Pre-load models to GPU (warm up)
    try:
        from core import get_transcriber, get_agent
        logger.info("Pre-loading transcriber...")
        get_transcriber()
        logger.info("Pre-loading agent...")
        get_agent()
        logger.info("[OK] All systems initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Multi-Agentic RE Tool Backend Shutting Down")
    logger.info("Cleaning up GPU resources...")


# ============ FastAPI App ============

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Multi-Agentic AI pipeline for automated requirements engineering.
    
    **Features:**
    - Real-time audio streaming with transcription via Faster-Whisper
    - Requirement analysis via local Ollama LLM (Llama 3)
    - Human-in-the-Loop interrupts for clarification
    - Context injection from PDF documents
    - ISO 29148 compliance formatting
    - Automatic Jira/Trello ticket generation
    
    **Optimized for:** RTX 4070 Super with float16 precision
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ============ Middleware ============

# CORS - Allow all origins (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Routes ============

app.include_router(router, prefix="/api", tags=["requirements"])


# ============ Root Endpoints ============

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Multi-Agentic Requirements Engineering Backend",
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.get("/api/info")
async def info():
    """Detailed system information."""
    return {
        "system": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
        "gpu": {
            "device": "RTX 4070 Super",
            "vram": "12GB",
            "inference_engines": ["Whisper (float16)", "Ollama LLM"],
        },
        "models": {
            "transcription": f"Faster-Whisper {settings.WHISPER_MODEL_SIZE}",
            "llm": f"{settings.OLLAMA_MODEL}",
        },
        "services": {
            "transcriber": "Ready",
            "agent_squad": "Ready",
            "export": "Ready",
        },
        "features": [
            "Real-time audio streaming",
            "File upload & processing",
            "Context injection",
            "Human-in-the-Loop",
            "ISO 29148 formatting",
            "Jira integration",
            "Trello integration",
        ],
    }


# ============ Main ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        workers=settings.FASTAPI_WORKERS,
        reload=settings.DEBUG,
        log_level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    )
