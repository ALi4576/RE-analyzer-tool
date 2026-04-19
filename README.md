# Multi-Agentic Requirements Engineering Tool

> **Automated requirements engineering pipeline using RTX 4070 Super, Faster-Whisper transcription, and Ollama-powered AI agents with Human-in-the-Loop interrupts.**

## 🎯 Overview

This backend system orchestrates a sophisticated multi-agent pipeline for requirements engineering:

1. **Ingestion**: Live WebSocket audio streams + PDF/document uploads
2. **Transcription**: Real-time with Faster-Whisper (CTranslate2)
3. **Analysis**: LLM-powered agent squad detecting requirement smells & gaps
4. **Verification**: Context injection from PDFs as ground truth
5. **Refinement**: Human-in-the-Loop for ambiguous requirements
6. **Formalization**: Automatic ISO 29148 compliance formatting
7. **Export**: Direct Jira/Trello ticket generation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Flutter/React)                                   │
│  - Microphone stream                                        │
│  - File uploads (PDFs)                                      │
│  - Clarification UI (WebSocket)                             │
└────────────────┬────────────────────────────────────────────┘
                 │ WebSocket / REST
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI BACKEND (async/await)                              │
│                                                              │
│  ┌─── WebSocket Handler ───────────────────────────────┐   │
│  │ • Audio chunk buffering                     │
│  │ • Real-time transcription                   │
│  │ • HITL interrupt handling                   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─── Service Layer ────────────────────────────────┐   │
│  │ • StreamAudioService (PCM → Whisper)              │
│  │ • FileUploadService (PDF/Audio upload)            │
│  │ • DocumentReaderService (Context extraction)      │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─── Core Agents (LangGraph State Machine) ──────────┐   │
│  │  Parse Input → Detect Smells                        │   │
│  │       ↓                                              │   │
│  │  [Smell Score >= Threshold?]                        │   │
│  │  YES → Generate Questions → INTERRUPT & WAIT        │   │
│  │  NO  → Analyze Logic → Formalize → Export Ready     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─── Core Modules ─────────────────────────────────┐   │
│  │ • TranscriberEngine (Faster-Whisper)                │
│  │ • ContextInjectionManager (PDF ground truth)        │
│  │ • RequirementsAnalysisAgent (LLM + LangGraph)       │
│  │ • ISO29148Formalizer (Compliance formatter)         │
│  │ • ExportManager (Jira + Trello)                     │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────┬────────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    ╔═══════╗ ╔═══════╗ ╔═══════════╗
    ║Ollama ║ ║Whisper║ ║ (DB)      ║
    ║Llama3 ║ ║CTranslate2║         ║
    ╚═══════╝ ╚═══════╝ ╚═══════════╝
        GPU    GPU       Storage
```

## 🚀 Quick Start

### Prerequisites

```bash
# Graphics
- RTX 4070 Super (12GB VRAM)
- CUDA 11.8+
- cuDNN

# Services
- Ollama running locally on port 11434
  $ ollama pull llama3
  $ ollama serve

# OS
- Python 3.10+
- pip/conda
```

### Setup

```bash
# 1. Clone repository
cd f:\coding\RE_tool

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Start Ollama (in separate terminal)
ollama serve

# 6. Run backend
python main.py

# 7. Access API
# REST: http://localhost:8000/api/docs
# WebSocket: ws://localhost:8000/api/ws/stream/{session_id}
```

## 📡 API Endpoints

### REST Endpoints

#### Analysis
```http
POST /api/analyze
Content-Type: application/json

{
  "session_id": "uuid",
  "text": "The system shall...",
  "context_file_path": "/path/to/charter.pdf"  # Optional
}

Response:
{
  "session_id": "uuid",
  "status": "needs_clarification",
  "interrupt_needed": true,
  "clarification_questions": [
    {
      "question_id": "q1",
      "question": "What is the expected response time?",
      "context": "Performance requirement mentioned but not specified",
      "required_clarity": ["response_time", "unit"]
    }
  ]
}
```

#### Clarification
```http
POST /api/clarify
Content-Type: application/json

{
  "session_id": "uuid",
  "question_id": "q1",
  "user_response": "Less than 500ms for 95th percentile"
}
```

#### Transcription
```http
POST /api/transcribe
Content-Type: application/json

{
  "file_path": "/path/to/audio.wav",
  "language": "en"
}

Response:
{
  "text": "The user said...",
  "length": 1234,
  "language": "en"
}
```

#### File Upload
```http
POST /api/upload/document
Content-Type: multipart/form-data

file: <PDF_FILE>

Response:
{
  "session_id": "uuid",
  "file_path": "/data/uploads/session_id/charter.pdf",
  "summary": {
    "title": "Project Charter",
    "type": "pdf",
    "section_count": 12,
    "sections": [...]
  }
}
```

#### Export
```http
POST /api/export
Content-Type: application/json

{
  "session_id": "uuid",
  "export_target": "jira"
}

Response:
{
  "export_id": "uuid",
  "target": "jira",
  "ticket_ids": ["PROJ-123", "PROJ-124"],
  "status": "success",
  "url": "https://jira.com/browse/PROJ"
}
```

### WebSocket Endpoint

#### Connection
```
ws://localhost:8000/api/ws/stream/{session_id}?context_file=/path/to/pdf
```

#### Message Protocol

**Client → Server:**
```javascript
// Audio chunk
{
  "type": "audio_chunk",
  "data": "base64_encoded_pcm_audio",
  "chunk_number": 1
}

// Clarification response
{
  "type": "clarification_response",
  "questions": {
    "q1": "Less than 500ms",
    "q2": "User-facing action"
  }
}

// Finalize stream
{
  "type": "finalize"
}

// Check status
{
  "type": "status"
}
```

**Server → Client:**
```javascript
// Connection ready
{
  "type": "connection_ready",
  "session_id": "uuid",
  "context_loaded": true
}

// Chunk acknowledged with transcription
{
  "type": "chunk_ack",
  "chunk_number": 1,
  "transcription": "The system shall handle..."
}

// New transcription available
{
  "type": "transcription",
  "text": "...user's spoken words...",
  "accumulated_text": "Full accumulated speech"
}

// HITL Interrupt - requires clarification
{
  "type": "interrupt",
  "session_id": "uuid",
  "questions": [
    {
      "question_id": "q1",
      "question": "Is this a functional or non-functional requirement?",
      "context": "The requirement uses unclear language",
      "required_clarity": ["requirement_type"]
    }
  ],
  "analysis_state": {
    "smell_score": 0.82,
    "smells": [...]
  }
}

// Analysis complete
{
  "type": "analysis_complete",
  "status": "formal_draft",
  "analysis": {
    "iso_requirements": [...],
    "completeness_score": 0.91,
    "export_formats": ["json", "csv", "jira", "trello"]
  }
}

// Error
{
  "type": "error",
  "error": "Error message"
}
```

## 💡 Key Concepts

### Context Injection

When a user uploads a PDF (e.g., Project Charter) **before** speaking requirements, the system uses it as "Ground Truth":

```
PDF Content (Ground Truth)
     ↓
[AI Agent Analysis]
     ↓
- Verify spoken requirements against PDF
- Flag contradictions
- Identify missing referenced sections
- Request clarifications on conflicts
```

This prevents requirements from being analyzed "in a vacuum."

### Human-in-the-Loop Pattern

When analysis detects quality issues (smell score ≥ 0.7):

```
Analysis Running
     ↓
[Detect High Smell Score]
     ↓
State saved (LangGraph checkpoint)
     ↓
INTERRUPT: Send clarification questions to frontend
     ↓
[User responds via WebSocket]
     ↓
Resume workflow from exact checkpoint
     ↓
Continue analysis with clarified input
```

### ISO 29148 Compliance

Requirements are formatted with:

- **Unique ID**: REQ-0001, REQ-0002, ...
- **Shall Statement**: Imperative language ("The system shall...")
- **Rationale**: Business justification
- **Acceptance Criteria**: Measurable, testable conditions
- **Traceability**: Links to related requirements
- **Priority**: High/Medium/Low
- **Category**: Functional/Non-functional/Interface

## 📊 Data Models

### RequirementAnalysisState

Tracks the entire journey of a requirement:

```python
{
  "session_id": "uuid",
  "input_text": "Raw user input or transcribed speech",
  "context_docs": [
    {
      "extracted_text": "PDF content...",
      "key_sections": {...}
    }
  ],
  "analysis_results": {
    "status": "analyzing|needs_clarification|formal_draft",
    "smell_score": 0.75,
    "smells": [
      {
        "type": "ambiguous",
        "severity": 0.9,
        "location": "excerpt...",
        "recommendation": "..."
      }
    ]
  },
  "user_clarifications": {
    "q1": "User's answer to question 1"
  },
  "formalized": {
    "iso_requirements": [ISORequirement],
    "completeness_score": 0.91
  },
  "export_results": [ExportResult],
  "iteration_count": 2
}
```

### ISORequirement

Standard requirement format:

```python
{
  "requirement_id": "REQ-0001",
  "title": "User Authentication",
  "shall_statement": "The system shall authenticate users within 2 seconds",
  "rationale": "Prevents unauthorized access",
  "acceptance_criteria": [
    "✓ Valid credentials accepted",
    "✓ Invalid credentials rejected",
    "✓ Response time < 2s"
  ],
  "priority": "High",
  "category": "Functional",
  "traceability": ["REQ-0002", "REQ-0003"]
}
```

## 🔧 Configuration

Edit `.env`:

```bash
# GPU Settings
WHISPER_MODEL_SIZE=base           # tiny|base|small|medium|large
WHISPER_COMPUTE_TYPE=float16      # float32|float16
OLLAMA_MODEL=llama3               # Your LLM model

# Analysis Thresholds
SMELL_SCORE_THRESHOLD=0.7         # Interrupt if >= 0.7
LOGICAL_GAP_THRESHOLD=0.65

# Export Backends
JIRA_ENABLED=True
JIRA_SERVER_URL=...
JIRA_API_TOKEN=...
```

## 📈 Performance Optimization

### RTX 4070 Super Specifics

- **Whisper (float16)**: 1-2s for 1min audio
- **Ollama (Llama 3)**: 50-100 tokens/sec
- **Concurrent**: ~4-6 concurrent streams

### Resource Usage
- **VRAM**: 8-10GB (Whisper + LLM)
- **CPU**: 4-8 cores
- **Disk**: 50GB for models

### Optimization Tips

1. **Batch Processing**: Use file uploads for high volume
2. **Stream Buffering**: WebSocket sends ~5sec chunks
3. **Async I/O**: FastAPI handles concurrency
4. **Model Caching**: Loaded once, reused across requests

## 🔗 Integration Examples

### Python Client
```python
import asyncio
import websockets
import base64

async def stream_audio():
    async with websockets.connect(
        "ws://localhost:8000/api/ws/stream/my-session"
    ) as ws:
        # Send audio chunks
        with open("speech.wav", "rb") as f:
            chunk = f.read(3200)  # ~200ms at 16kHz
            await ws.send_json({
                "type": "audio_chunk",
                "data": base64.b64encode(chunk).decode(),
                "chunk_number": 1
            })
        
        # Wait for analysis
        response = await ws.recv()
        print(response)

asyncio.run(stream_audio())
```

### JavaScript Client (React)
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/ws/stream/${sessionId}`
);

// Send audio
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => {
      const reader = new FileReader();
      reader.onload = () => {
        ws.send(JSON.stringify({
          type: "audio_chunk",
          data: reader.result.split(',')[1],  // base64
          chunk_number: chunk_num++
        }));
      };
      reader.readAsDataURL(e.data);
    };
    recorder.start(200);  // 200ms chunks
  });

// Receive analysis
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === "interrupt") {
    // Show clarification UI
    showClarificationDialog(message.questions);
  }
};
```

## 📚 Project Structure

```
RE_tool/
├── main.py                    # FastAPI app entry
├── requirements.txt           # Dependencies
├── .env.example              # Configuration template
│
├── config/
│   ├── __init__.py
│   └── settings.py           # All configuration
│
├── core/
│   ├── __init__.py
│   ├── transcriber.py        # Faster-Whisper engine
│   ├── context_manager.py    # PDF context injection
│   ├── agents.py             # LangGraph orchestration
│   ├── formalize.py          # ISO 29148 formatter
│   └── exporter.py           # Jira/Trello export
│
├── services/
│   ├── __init__.py
│   ├── stream_service.py     # WebSocket audio streaming
│   ├── file_service.py       # File upload handler
│   └── reader_service.py     # Document reader
│
├── api/
│   ├── __init__.py
│   ├── routes.py             # REST endpoints
│   └── websocket_handler.py  # WebSocket logic
│
├── models/
│   ├── __init__.py
│   └── schemas.py            # Pydantic models
│
├── utils/
│   ├── __init__.py
│   └── logger.py             # Logging setup
│
└── data/
    ├── uploads/              # Temporary file storage
    └── checkpoints.db        # LangGraph state
```

## 🐛 Troubleshooting

### "Ollama connection refused"
```bash
1. Ensure Ollama is running:
   $ ollama serve

2. Check port 11434:
   $ netstat -an | findstr 11434

3. Verify model loaded:
   $ ollama list
```

### "CUDA out of memory"
```bash
1. Reduce Whisper model: WHISPER_MODEL_SIZE=tiny
2. Use float32 instead of float16: WHISPER_COMPUTE_TYPE=float32
3. Reduce concurrent streams
```

### "WebSocket connection refused"
```bash
1. Check CORS settings in main.py
2. Verify FastAPI is running on correct port
3. Check firewall/proxy settings
```

## 📝 Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Static analysis
python -m pytest tests/

# Transcription test
curl -X POST http://localhost:8000/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{"file_path": "sample.wav", "language": "en"}'
```

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y cuda-toolkit

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure CORS for specific origins
- [ ] Enable Jira/Trello authentication
- [ ] Set up SSL/TLS
- [ ] Configure logging aggregation
- [ ] Set resource limits
- [ ] Enable request rate limiting

## 📖 References

- [LangGraph Docs](https://python.langchain.com/docs/langgraph)
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper)
- [Ollama](https://ollama.ai)
- [ISO 29148](https://www.iso.org/standard/72089.html)
- [FastAPI](https://fastapi.tiangolo.com)

## 📄 License

Proprietary - Requirements Engineering Tool

---

**Built with ❤️ for advanced requirements engineering**
