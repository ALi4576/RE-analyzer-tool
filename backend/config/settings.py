"""
Configuration and environment settings for the RE Tool backend.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""
    
    # App
    APP_NAME = "Multi-Agentic RE Tool"
    APP_VERSION = "0.1.0"
    DEBUG = os.getenv("DEBUG", "True") == "True"
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", 0.7))
    # Low temperature for deterministic ISO formalization output
    OLLAMA_FORMALIZE_TEMPERATURE = float(os.getenv("OLLAMA_FORMALIZE_TEMPERATURE", 0.1))
    # Smaller/faster model for quality analysis (smell + gap scoring).
    # Set to e.g. "phi3:mini" or "gemma2:2b" to cut analysis latency.
    # Defaults to the main model so it works out of the box.
    OLLAMA_ANALYSIS_MODEL = os.getenv("OLLAMA_ANALYSIS_MODEL", "")
    
    # Faster-Whisper Configuration
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny, base, small, medium, large
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
    
    # Audio/Stream Configuration
    SAMPLE_RATE = 16000
    AUDIO_CHUNK_SIZE = 3200  # 200ms at 16kHz
    MAX_AUDIO_DURATION = 300  # 5 minutes
    SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "m4a", "ogg", "flac"]
    
    # File Upload Configuration
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
    SUPPORTED_FILE_TYPES = ["pdf", "txt", "doc", "docx", "wav", "mp3", "m4a", "ogg", "flac", "webm"]
    
    # PDF Processing
    PDF_EXTRACTION_MODEL = "pymupdf"  # PyMuPDF for fast extraction
    
    # Context Injection
    CONTEXT_WINDOW_SIZE = 4000  # Tokens to preserve from context
    CONTEXT_RETENTION_SCORE_THRESHOLD = 0.6
    
    # Requirements Analysis
    SMELL_SCORE_THRESHOLD = 0.7  # Trigger interrupt if >= 0.7
    LOGICAL_GAP_THRESHOLD = 0.65
    
    # ISO 29148 Compliance
    ISO_29148_TEMPLATE_VERSION = "2023"
    
    # Jira Configuration
    JIRA_ENABLED = os.getenv("JIRA_ENABLED", "True") == "True"
    JIRA_SERVER_URL = os.getenv("JIRA_SERVER_URL", "")
    JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")
    
    # Trello Configuration
    TRELLO_ENABLED = os.getenv("TRELLO_ENABLED", "True") == "True"
    TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "")
    TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN", "")
    TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID", "")
    
    # LangGraph State Management
    CHECKPOINTER_TYPE = os.getenv("CHECKPOINTER_TYPE", "memory")  # memory, sqlite, postgres
    CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "data/checkpoints.db")
    
    # FastAPI
    FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
    FASTAPI_WORKERS = int(os.getenv("FASTAPI_WORKERS", 1))  # >1 would load Whisper/Ollama N times → VRAM OOM
    
    # WebSocket Settings
    WEBSOCKET_TIMEOUT = 300  # 5 minutes
    WEBSOCKET_QUEUE_SIZE = 100


settings = Settings()
