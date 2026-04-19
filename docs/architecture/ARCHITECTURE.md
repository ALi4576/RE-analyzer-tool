# Technical Architecture Documentation

## System Design Overview

This document provides deep technical detail on the Multi-Agentic Requirements Engineering Tool architecture.

## 1. GPU-Optimized Inference Layer

### 1.1 FastAPI + Uvicorn + ASGI

The backend uses **ASGI** (Asynchronous Server Gateway Interface) to handle concurrent requests non-blocking:

```python
# Non-blocking concurrent request handling
async def analyze_requirements(request):
    # This doesn't block the event loop
    # GPU operations run in executor threads
    result = await asyncio.to_thread(
        agent.analyze,  # CPU-bound
        state
    )
    return result
```

**Benefits:**
- 1000+ concurrent WebSocket connections
- Fast I/O for file uploads
- Responsive to user interrupts

### 1.2 CUDA Acceleration

Both Faster-Whisper and Ollama leverage RTX 4070 Super:

#### Faster-Whisper Configuration
```python
WhisperModel(
    "base",                    # 74M parameters
    device="cuda",             # GPU inference
    compute_type="float16",    # 12GB VRAM efficiency
    num_workers=2              # Parallel processing
)
```

**Performance:** 1 minute audio → 1-2 seconds

#### Ollama Configuration
```
Model: llama3              # 70B parameters
Quantization: q4_K_M       # 4-bit for VRAM efficiency
GPU Layers: ALL            # Full GPU acceleration
```

**Performance:** 50-100 tokens/second

### 1.3 Memory Management

```
RTX 4070 Super Allocation:
├── Faster-Whisper Base: 2.5 GB
├── Ollama LLM: 8-9 GB
├── LangGraph State: 500 MB
├── Buffers/Caches: 1 GB
└── Available for spikes: 0.5 GB
```

## 2. Audio Processing Pipeline

### 2.1 WebSocket Stream Handling

```
Client (Browser)
    │
    └─→ [50ms PCM chunks]
        │
        ├─→ WebSocket Server
        │   (async listener)
        │
        ├─→ StreamAudioService
        │   (accumulate chunks)
        │
        ├─→ [When 5sec buffered]
        │   └─→ Faster-Whisper
        │       (transcribe)
        │
        └─→ Send transcription
            back to client
```

### 2.2 Audio Buffering Strategy

```python
class AudioStreamBuffer:
    def __init__(self, chunk_size=3200):
        self.audio_data = bytearray()       # Accumulator
        self.total_duration = 0.0
    
    async def add_chunk(self, audio_bytes):
        self.audio_data.extend(audio_bytes)
        self.total_duration += len(audio_bytes) / 32000
        
        # Trigger transcription at 5 seconds
        if self.total_duration >= 5.0:
            return self.transcribe_buffered()
```

**Why 5 seconds?**
- Faster-Whisper needs minimum context
- Keeps VRAM usage stable
- Provides ~1-2s latency
- Allows natural speech pausing

### 2.3 Real-Time Transcription Loop

```
┌─────────────────────────────────────┐
│ Client speaks into microphone        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Browser MediaRecorder captures PCM  │
│ (50ms chunks at 16kHz)              │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ WebSocket sends binary chunks       │
│ {type: "audio_chunk", data: b64}    │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ FastAPI WebSocket Handler           │
│ (asyncio listener)                  │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ StreamAudioService buffers chunks   │
│ (accumulates to 5 sec)              │
└──────────┬──────────────────────────┘
           │
       [5 sec accumulated]
           │
           ▼
┌─────────────────────────────────────┐
│ asyncio.to_thread(Whisper.transcribe)
│ (GPU processing in executor)        │
└──────────┬──────────────────────────┘
           │ [1-2 sec processing]
           │
           ▼
┌─────────────────────────────────────┐
│ Transcription callback triggered    │
│ Send to frontend + analysis agent   │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Analysis Agent analyzes text        │
│ (parallel with next audio)          │
└─────────────────────────────────────┘
```

## 3. LangGraph Orchestration

### 3.1 Stateful Workflow Graph

```python
workflow = StateGraph(RequirementAnalysisState)

# Nodes (agent actions)
workflow.add_node("parse_input", parse_node)
workflow.add_node("detect_smells", smell_node)
workflow.add_node("analyze_logic", logic_node)
workflow.add_node("generate_questions", questions_node)
workflow.add_node("formalize", formalize_node)

# Edges define flow
workflow.add_edge("parse_input", "detect_smells")
workflow.add_conditional_edges(
    "detect_smells",
    should_interrupt,      # Decision function
    {
        True: "generate_questions",   # High quality issues
        False: "analyze_logic"        # OK to proceed
    }
)

graph = workflow.compile(checkpointer=MemorySaver())
```

### 3.2 State Machine Architecture

```
START
  │
  ▼
┌─────────────────────┐
│ Parse Input Node    │
│ - Extract entities  │      ┌──────────────────┐
│ - Normalize text    │─────→│ Input parsed     │
└─────────────────────┘      └──────────────────┘
  │
  ▼
┌─────────────────────┐
│ Detect Smells Node  │      ┌──────────────────┐
│ - Quality issues    │─────→│ Smell score: 0.8 │
│ - Rate severity     │      │ 3 issues found   │
└─────────────────────┘      └──────────────────┘
  │
  ├─── (score >= 0.7) ──→ INTERRUPT
  │                         │
  │                         ▼
  │                    ┌──────────────────┐
  │                    │ Generate Questions│
  │                    │ Topic: "unclear"  │
  │                    └─────────┬────────┘
  │                              │
  │                         [PAUSE STATE]
  │                    Await user response
  │                              │
  │                    ┌─────────▼────────┐
  │                    │Resume with answers│
  │                    │Update input text  │
  │                    └─────────┬────────┘
  │                              │
  ├───────────────────────────────┘
  │
  ▼
┌─────────────────────┐
│ Analyze Logic Node  │      ┌──────────────────┐
│ - Find gaps         │─────→│ Logic gaps: 2    │
│ - Check conflicts   │      │ Consistency: 0.9 │
└─────────────────────┘      └──────────────────┘
  │
  ▼
┌─────────────────────┐
│ Formalize Node      │      ┌──────────────────┐
│ - ISO 29148 format  │─────→│ REQ-0001         │
│ - Add traceability  │      │ REQ-0002         │
└─────────────────────┘      │ ... (5 total)    │
  │                           └──────────────────┘
  ▼
┌─────────────────────┐
│ Export Ready Node   │      ┌──────────────────┐
│ - Mark complete     │─────→│ Status: complete │
│ - Set export flag   │      │ Ready for Jira   │
└─────────────────────┘      └──────────────────┘
  │
  ▼
 END
```

### 3.3 Checkpoint & Resume (HITL)

```python
# Run initial workflow
initial_result = graph.invoke(
    state,
    config={"configurable": {"thread_id": session_id}}
)
# ↓ Checkpointer saves state

if initial_result["interrupt_needed"]:
    # Send questions to frontend, wait for response
    # ...
    
    # Resume from checkpoint
    resumed_result = graph.invoke(
        Command(resume=user_clarifications),
        config={"configurable": {"thread_id": session_id}}
    )
    # ↓ Continues exactly where it paused
```

**Key Files Involved:**
- `config/settings.py`: `CHECKPOINTER_TYPE` and `CHECKPOINT_DB_PATH`
- `core/agents.py`: Graph definition and node implementations

## 4. Context Injection Architecture

### 4.1 PDF Ground Truth

```
User uploads charter.pdf
        │
        ▼
┌──────────────────────────┐
│ DocumentReaderService    │
│ - PyMuPDF extraction     │
│ - Structure preservation │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ ContextInjectionPayload  │
│ {                        │
│   extracted_text: "..." │
│   key_sections: {...}   │
│   document_title: "..." │
│ }                        │
└────────┬─────────────────┘
         │
    [CACHE in memory]
         │
User speaks requirement
         ▼
┌──────────────────────────────────┐
│ Context Injection Manager        │
│ create_injection_prompt()        │
│ - Prepend PDF context            │
│ - Mark as GROUND TRUTH           │
│ - Include key sections           │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Enhanced Prompt to LLM           │
│ "Given this context...           │
│  Verify if the requirement:      │
│  [user's spoken requirement]     │
│  aligns with the charter."       │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ LLM Analysis                     │
│ - Checks for contradictions      │
│ - Flags new scope creep          │
│ - Maps to existing sections      │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Result                           │
│ "Requirement X contradicts       │
│  Section 2.3 of charter.         │
│  Clarification needed."          │
└────────────────────────────────────┘
```

### 4.2 Key Sections Extraction

```python
# For PDFs
blocks = page.get_blocks()
for block in blocks:
    text = block[4]
    if is_likely_header(text):
        key_sections[f"Section_{page}"] = text

# Result:
key_sections = {
    "Section_0": "Project Objectives",
    "Section_0": "Stakeholder Requirements",
    "Section_1": "Technical Constraints",
    # ... etc
}
```

## 5. Multi-Agent Squad Design

### 5.1 Agent Specialization

Each node in the LangGraph represents an agent:

1. **Parser Agent** (Node: `parse_input`)
   - Input: Raw text/speech
   - Output: Structured entities
   - Tools: LLM for NLP

2. **Smell Detector Agent** (Node: `detect_smells`)
   - Input: Parsed requirements
   - Output: Quality issues + scores
   - Tools: LLM with requirement knowledge base
   
   ```python
   SMELL_TYPES = [
       "ambiguous",
       "incomplete",
       "infeasible",
       "conflicting",
       "unmeasurable",
       "vague_scope",
       "missing_rationale"
   ]
   ```

3. **Logic Analyzer Agent** (Node: `analyze_logic`)
   - Input: Requirement text
   - Output: Gap score + conflicts
   - Tools: LLM reasoning

4. **Clarifier Agent** (Node: `generate_questions`)
   - Input: Issues found
   - Output: Targeted questions
   - Tools: Question generation LLM

5. **Formalizer Agent** (Node: `formalize`)
   - Input: Clarified requirements
   - Output: ISO 29148 compliant requirements
   - Tools: Template engine + LLM

### 5.2 Agent Communication

```python
# State flows through agents
state = {
    "session_id": "...",
    "input_text": "User's raw requirement",
    "parsed_analysis": "Parser output",
    "smells": [RequirementSmell, ...],
    "smell_score": 0.75,
    "logical_gap_score": 0.45,
    "clarification_questions": [ClarificationQuestion, ...],
    "user_clarifications": {"q1": "answer1", ...},
    "iso_requirements": [ISORequirement, ...],
    "status": "formal_draft"
}
```

## 6. ISO 29148 Compliance Engine

### 6.1 Requirement Anatomy

ISO 29148 defines a requirement as:

```
┌─────────────────────────────┐
│ REQ-0001                    │ ← Unique Identifier
├─────────────────────────────┤
│ User Authentication         │ ← Clear Title
├─────────────────────────────┤
│ The system shall             │
│ authenticate users within 2s │ ← Testable Shall-Statement
├─────────────────────────────┤
│ Prevents unauthorized access │ ← Business Rationale
├─────────────────────────────┤
│ ✓ Valid credentials accepted │ ← Acceptance Criteria
│ ✓ Invalid credentials failed │   (measurable)
│ ✓ Response < 2s              │
├─────────────────────────────┤
│ High                         │ ← Priority
├─────────────────────────────┤
│ Functional                   │ ← Category
├─────────────────────────────┤
│ REQ-0002, REQ-0003          │ ← Traceability
└─────────────────────────────┘
```

### 6.2 Formalization Process

```python
def formalize_requirement(text):
    # 1. Extract from messy text
    title = extract_title(text)
    
    # 2. Convert to imperative (shall)
    shall = create_shall_statement(text)
    # "The user can login" → "The system shall authenticate users"
    
    # 3. Extract/generate rationale
    rationale = extract_or_generate_rationale(text)
    
    # 4. Create measurable criteria
    criteria = generate_acceptance_criteria(text)
    
    # 5. Determine priority
    priority = analyze_priority(text)
    
    # 6. Classify
    category = classify_requirement(text)
    
    return ISORequirement(
        requirement_id=next_id(),
        title=title,
        shall_statement=shall,
        rationale=rationale,
        acceptance_criteria=criteria,
        priority=priority,
        category=category,
        traceability=[]
    )
```

## 7. Export Architecture

### 7.1 Jira Integration

```python
from jira import JIRA

client = JIRA(
    server="https://jira.company.com",
    auth=(username, api_token)
)

# For each ISO requirement
for req in formalized.iso_requirements:
    issue = client.create_issue(
        project="PROJ",
        issuetype="Story",
        summary=req.title,
        description=format_jira_description(req),
        priority=map_priority(req.priority),
        customfield_10000=req.requirement_id
    )
    # Returns: PROJ-123
```

### 7.2 Trello Integration

```python
from trello import TrelloClient

client = TrelloClient(api_key=key, api_secret=secret)
board = client.get_board(board_id)
list = board.add_list("Requirements")

# For each ISO requirement
for req in formalized.iso_requirements:
    card = list.add_card(
        name=req.title,
        desc=format_trello_description(req)
    )
    # Returns: card ID
```

## 8. Error Handling & Recovery

### 8.1 Graceful Degradation

```python
try:
    # Primary: GPU-accelerated
    text = transcriber.transcribe_file(path)
except CudaError:
    # Fallback: CPU transcription (slower)
    logger.warning("GPU transcription failed, using CPU")
    text = cpu_transcriber.transcribe_file(path)
```

### 8.2 State Recovery

```python
# If process crashes mid-analysis
if checkpointer.get_state(session_id):
    # Resume from checkpoint
    state = checkpointer.get_state(session_id)
    result = graph.invoke(
        Command(resume=state),
        config={"thread_id": session_id}
    )
```

## 9. Performance Optimization

### 9.1 Caching Strategy

```python
# Context caching
self.extracted_contexts = {
    "/path/to/file.pdf": ContextInjectionPayload(...)
}

# Model caching (global singleton)
_transcriber = None
_agent = None
_formalizer = None
# Loaded once, reused across requests
```

### 9.2 Async I/O Optimization

```python
# Multiple concurrent requests handled efficiently
async def analyze_requirements(request):
    # I/O-bound: file read
    context = await read_file(request.context_file)
    
    # CPU-bound but async
    analysis = await asyncio.to_thread(
        agent.analyze,
        state
    )
    
    return analysis
# While waiting for analysis, other requests processed
```

### 9.3 GPU Memory Management

```python
# Pre-load models on startup
@app.lifespan
async def lifespan(app):
    # Warm up caches
    get_transcriber()
    get_agent()
    
    yield
    
    # Cleanup on shutdown
    # (Auto garbage collected)
```

## 10. Security Considerations

### 10.1 Authentication (Future)

```python
# Current: Open for development
# Production: Add JWT/OAuth2

from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/analyze")
async def analyze(request, token: str = Depends(security)):
    # Verify token
    user = verify_token(token)
    # ...
```

### 10.2 Input Validation

```python
# Pydantic validates all inputs
class AnalyzeRequirementsRequest(BaseModel):
    session_id: str = Field(..., max_length=50)
    text: str = Field(..., max_length=50000)
    context_file_path: Optional[str] = Field(None, max_length=500)

# FastAPI auto-validates before handler
```

### 10.3 File Upload Security

```python
# Validate file
await validate_file(file)  # Extension, size, type

# Store in session directory
session_dir = uploads / session_id
file_path = session_dir / filename

# Cleanup after export
cleanup_session_files(session_id)
```

## 11. Monitoring & Observability

### 11.1 Structured Logging

```python
logger = get_logger("agent")
logger.info(f"Analysis started for {session_id}")
logger.debug(f"Smell score: {score:.2f}")
logger.warning(f"Fallback to CPU: {error}")
logger.error(f"Critical failure: {error}")
```

### 11.2 Metrics to Track

- Transcription latency
- Analysis latency
- GPU memory usage
- Concurrent connections
- Error rates by component
- Export success rate

### 11.3 Health Checks

```http
GET /api/health

Response:
{
  "status": "healthy",
  "services": {
    "transcriber": "ready",
    "agent": "ready",
    "exporter": "ready"
  }
}
```

---

This technical documentation provides the detailed architectural patterns, data flows, and implementation details of the system.
