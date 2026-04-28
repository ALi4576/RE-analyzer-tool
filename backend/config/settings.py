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

    # ============ LLM Provider Configuration ============
    # Per-role provider switching. Each LLM role (main, analysis, formalize) can
    # independently target any of: ollama | openai | anthropic | gemini.
    # If a *_LLM_PROVIDER is unset, it falls back to "ollama" and uses the
    # corresponding OLLAMA_* model/temperature settings (full backward compat).
    #
    # Cloud API keys are only required when that provider is selected.
    SUPPORTED_LLM_PROVIDERS = ("ollama", "openai", "anthropic", "gemini")

    # --- Main role (clarification question generation) ---
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
    LLM_MODEL = os.getenv("LLM_MODEL", "")  # empty -> falls back to OLLAMA_MODEL when provider=ollama

    # --- Analysis role (smell + gap scoring) ---
    ANALYSIS_LLM_PROVIDER = os.getenv("ANALYSIS_LLM_PROVIDER", "").lower()  # empty -> inherit LLM_PROVIDER
    ANALYSIS_LLM_MODEL = os.getenv("ANALYSIS_LLM_MODEL", "")

    # --- Formalize role (ISO 29148 atomization) ---
    FORMALIZE_LLM_PROVIDER = os.getenv("FORMALIZE_LLM_PROVIDER", "").lower()  # empty -> inherit LLM_PROVIDER
    FORMALIZE_LLM_MODEL = os.getenv("FORMALIZE_LLM_MODEL", "")

    # --- Cloud provider API keys (only required when that provider is selected) ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")  # optional, for Azure / proxies
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # --- Main model (clarification question generation) ---
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "512"))

    # --- Analysis model (smell detection + gap scoring, runs on every request) ---
    # Leave empty to inherit OLLAMA_MODEL. Set to a smaller/faster model
    # (e.g. phi3:mini, gemma2:2b) to cut per-request latency.
    OLLAMA_ANALYSIS_MODEL = os.getenv("OLLAMA_ANALYSIS_MODEL", "")
    OLLAMA_ANALYSIS_TEMPERATURE = float(os.getenv("OLLAMA_ANALYSIS_TEMPERATURE", "0.1"))
    OLLAMA_ANALYSIS_NUM_PREDICT = int(os.getenv("OLLAMA_ANALYSIS_NUM_PREDICT", "512"))

    # --- Formalize model (ISO 29148 atomization, user-facing output) ---
    # Leave empty to inherit OLLAMA_MODEL. Set to a larger/higher-quality model
    # (e.g. qwen2.5:14b-instruct-q4_K_M) for tighter ISO output without
    # slowing down question generation.
    OLLAMA_FORMALIZE_MODEL = os.getenv("OLLAMA_FORMALIZE_MODEL", "")
    OLLAMA_FORMALIZE_TEMPERATURE = float(os.getenv("OLLAMA_FORMALIZE_TEMPERATURE", "0.1"))
    OLLAMA_FORMALIZE_NUM_PREDICT = int(os.getenv("OLLAMA_FORMALIZE_NUM_PREDICT", "2048"))
    
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

    # Iterative Clarification Loop
    # Stop iterating clarification rounds once overall quality reaches this score.
    QUALITY_TARGET_SCORE = float(os.getenv("QUALITY_TARGET_SCORE", "0.9"))
    # Hard cap on the number of clarification rounds before forcing export
    # regardless of quality (prevents infinite loops if the LLM cannot reach the target).
    MAX_CLARIFICATION_ROUNDS = int(os.getenv("MAX_CLARIFICATION_ROUNDS", "3"))
    
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
