# RE_tool — Multi-Agentic Requirements Engineering Tool

> Automated requirements engineering pipeline that ingests live audio or documents, detects requirement smells with local LLM agents, runs a Human-in-the-Loop clarification loop, and exports ISO 29148-compliant tickets to Jira or Trello.

## Overview

- **Ingest** live microphone streams (WebSocket) or PDF/document uploads.
- **Transcribe** speech in real time with Faster-Whisper (CTranslate2, GPU).
- **Analyze** transcripts through a LangGraph agent squad backed by local Ollama models — detecting ambiguity, gaps, and contradictions.
- **Clarify** through a Human-in-the-Loop interrupt: workflow pauses, asks questions, then resumes from the exact checkpoint.
- **Formalize** outputs to the ISO 29148 standard and **export** directly to Jira or Trello.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React — Web_Frontend/)                            │
│  - Microphone stream                                         │
│  - File uploads (PDFs)                                       │
│  - Clarification UI (WebSocket)                              │
└────────────────┬────────────────────────────────────────────┘
                 │ WebSocket / REST
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI BACKEND (async/await)                               │
│                                                              │
│  ┌─── WebSocket Handler ──────────────────────────────┐    │
│  │ • Audio chunk buffering                             │    │
│  │ • Real-time transcription                           │    │
│  │ • HITL interrupt handling                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─── Service Layer ──────────────────────────────────┐    │
│  │ • StreamAudioService (PCM → Whisper)                │    │
│  │ • FileUploadService (PDF/Audio upload)              │    │
│  │ • DocumentReaderService (Context extraction)        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─── Core Agents (LangGraph State Machine) ──────────┐    │
│  │  Parse Input → Detect Smells                        │    │
│  │       ↓                                              │    │
│  │  [Smell Score >= Threshold?]                        │    │
│  │  YES → Generate Questions → INTERRUPT & WAIT        │    │
│  │  NO  → Analyze Logic → Formalize → Export Ready     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─── Core Modules ───────────────────────────────────┐    │
│  │ • TranscriberEngine (Faster-Whisper)                │    │
│  │ • ContextInjectionManager (PDF ground truth)        │    │
│  │ • RequirementsAnalysisAgent (LLM + LangGraph)       │    │
│  │ • ISO29148Formalizer (Compliance formatter)         │    │
│  │ • ExportManager (Jira + Trello)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────┬────────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    ╔═══════╗ ╔═══════╗ ╔═══════════╗
    ║Ollama ║ ║Whisper║ ║ (DB)      ║
    ║Llama3 ║ ║CT2    ║ ║ Storage   ║
    ╚═══════╝ ╚═══════╝ ╚═══════════╝
        GPU      GPU
```

For a deeper walkthrough, see [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md).

## Prerequisites

- **GPU**: NVIDIA GPU with 8GB+ VRAM (originally tuned for RTX 4070 Super, 12GB)
- **CUDA**: 11.8+ with cuDNN
- **Python**: 3.10 or newer
- **Ollama**: running locally on port `11434` with at least one model pulled (e.g. `ollama pull llama3`)
- **Node.js**: 18+ (only required if running the React frontend)

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # macOS/Linux

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Configure environment
cp backend/.env.example backend/.env
# edit backend/.env with your values

# 4. Start Ollama in a separate terminal
ollama serve

# 5. Run the backend
python main.py
```

The API is then served at `http://localhost:8000/api/docs` (Swagger UI) and `ws://localhost:8000/api/ws/stream/{session_id}`.

For the full walkthrough (frontend, troubleshooting, alternative setups), see [docs/setup/GETTING_STARTED.md](docs/setup/GETTING_STARTED.md) or the leaner [docs/setup/QUICK_START_NO_DOCKER.md](docs/setup/QUICK_START_NO_DOCKER.md).

## Key Concepts

### Context Injection

When a user uploads a PDF (e.g. a project charter) before speaking, the system treats that document as ground truth. Spoken requirements are validated against the PDF — contradictions are flagged, missing referenced sections are identified, and the agent will ask for clarification on conflicts. This avoids analyzing requirements "in a vacuum."

### Human-in-the-Loop (HITL)

When the smell score crosses the configured threshold, the LangGraph workflow checkpoints its state, sends clarification questions over the WebSocket, and waits. Once the user responds, execution resumes from the exact checkpoint with the clarified input — no replay of prior work. See the architecture doc for state machine details.

### ISO 29148 Compliance

Every formalized requirement carries a unique ID, an imperative "shall" statement, rationale, measurable acceptance criteria, traceability links, priority, and category (Functional / Non-functional / Interface). This makes outputs directly consumable by Jira/Trello and audit-ready.

## Configuration

All runtime configuration lives in `backend/.env` (template: [`backend/.env.example`](backend/.env.example)). Key variables:

```bash
# ============ LLM Provider Configuration ============
LLM_PROVIDER=ollama          # main/fallback role  (ollama | openai | anthropic | google)
LLM_MODEL=                   # main model name

# Role-specific overrides (inherit LLM_PROVIDER / LLM_MODEL when left empty)
ANALYSIS_LLM_PROVIDER=       # smell/gap detection role
ANALYSIS_LLM_MODEL=          # model for smell/gap role
FORMALIZE_LLM_PROVIDER=      # ISO formalize role
FORMALIZE_LLM_MODEL=         # model for ISO formalize role

# API keys (only required for the providers you use)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# GOOGLE_API_KEY=

# Ollama (used when LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Whisper
WHISPER_MODEL_SIZE=base       # tiny | base | small | medium | large
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# LangGraph checkpointing
CHECKPOINTER_TYPE=memory      # memory | sqlite | postgres

# Export integrations
JIRA_ENABLED=True
TRELLO_ENABLED=True
```

Role-specific providers (`ANALYSIS_LLM_PROVIDER`, `FORMALIZE_LLM_PROVIDER`) inherit `LLM_PROVIDER` when left empty — set them only when you want a different model for smell detection or ISO formalization than the main role.

### Switching LLM provider

The backend supports four providers behind a unified interface. Pick one and set the matching `.env` snippet. The non-Ollama providers require an extra pip install (kept optional so the base install stays slim).

**Ollama (default — local, no API key)**

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

**OpenAI**

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```
```bash
pip install langchain-openai
```

**Anthropic**

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=...
```
```bash
pip install langchain-anthropic
```

**Google**

```bash
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=...
```
```bash
pip install langchain-google-genai
```

## API Reference

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/analyze` | Run an analysis pass on text input (optionally with a context PDF). |
| `POST` | `/api/clarify` | Submit a user response to a HITL clarification question. |
| `POST` | `/api/transcribe` | Transcribe an audio file via Faster-Whisper. |
| `POST` | `/api/upload/document` | Upload a PDF/document for context injection. |
| `POST` | `/api/export` | Export formalized requirements to Jira or Trello. |
| `GET` | `/api/health` | Health check. |
| `WS` | `/api/ws/stream/{session_id}` | Live audio streaming + HITL clarification channel. |

Full request/response schemas are available in the auto-generated Swagger UI at `/api/docs`. WebSocket message protocol details are in [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md).

## Project Structure

```
RE_tool/
├── main.py                     # FastAPI app entry
├── requirements.txt            # Backend dependencies
├── backend/
│   ├── .env.example            # Configuration template
│   ├── api/                    # REST routes + WebSocket handler
│   ├── config/                 # settings.py
│   ├── core/                   # transcriber, agents, formalizer, exporter
│   ├── services/               # stream, file upload, document reader
│   ├── models/                 # Pydantic schemas
│   ├── utils/                  # logging
│   └── data/                   # uploads/, checkpoints.db
├── Web_Frontend/               # React frontend (see its README)
├── docs/                       # Setup, architecture, testing, project docs
└── graphify-out/               # Knowledge graph artifacts
```

## Troubleshooting

**`Ollama connection refused`** — make sure `ollama serve` is running, port `11434` is free, and the configured model is pulled (`ollama list`).

**`CUDA out of memory`** — reduce `WHISPER_MODEL_SIZE` (e.g. `tiny`), switch `WHISPER_COMPUTE_TYPE` to `float32`, or lower the number of concurrent streams.

**`WebSocket connection refused`** — check CORS in `main.py`, confirm FastAPI is bound to the expected port, and verify firewall/proxy settings.

## Documentation Index

| Document | Description |
| --- | --- |
| [docs/setup/GETTING_STARTED.md](docs/setup/GETTING_STARTED.md) | Full environment setup walkthrough. |
| [docs/setup/QUICK_START_NO_DOCKER.md](docs/setup/QUICK_START_NO_DOCKER.md) | Minimal no-Docker quick start. |
| [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | System architecture deep-dive. |
| [docs/architecture/ARCHITECTURE_FIX.md](docs/architecture/ARCHITECTURE_FIX.md) | Architecture notes and fixes. |
| [docs/project/PROJECT_SUMMARY.md](docs/project/PROJECT_SUMMARY.md) | High-level project summary. |
| [docs/project/IMPLEMENTATION_COMPLETE.md](docs/project/IMPLEMENTATION_COMPLETE.md) | Implementation status. |
| [docs/project/CODE_AUDIT.md](docs/project/CODE_AUDIT.md) | Code audit report. |
| [docs/project/PERFORMANCE_AND_ARCH_COMPARISON.md](docs/project/PERFORMANCE_AND_ARCH_COMPARISON.md) | Performance and architecture comparison. |
| [docs/testing/TESTING_GUIDE.md](docs/testing/TESTING_GUIDE.md) | Full test suite guide. |
| [docs/testing/TESTING_QUICK_START.md](docs/testing/TESTING_QUICK_START.md) | Quick test reference. |
| [docs/testing/PROMPT_TESTING.md](docs/testing/PROMPT_TESTING.md) | Prompt-level testing guide. |
| [Web_Frontend/README.md](Web_Frontend/README.md) | Frontend-specific docs. |

## License

Proprietary — Requirements Engineering Tool.
