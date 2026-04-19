# Getting Started Guide

## 🚀 60-Second Startup

### Prerequisites
- **GPU**: RTX 4070 Super (or any RTX card with CUDA support)
- **OS**: Windows 10/11
- **Software**: Python 3.10+, Ollama

### Steps

#### 1. Start Ollama (Terminal 1)
```powershell
# Download and start Ollama
ollama pull llama3
ollama serve
# Listens on http://localhost:11434
```

#### 2. Setup Backend (Terminal 2)
```powershell
cd f:\coding\RE_tool

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies (first time ~5 minutes)
pip install -r requirements.txt

# Copy environment config
copy .env.example .env

# Run setup script (optional, helps with initial checks)
python setup.py
```

#### 3. Start Backend
```powershell
# Still in venv
python main.py

# Output should show:
# ✓ Whisper model loaded
# ✓ LangGraph initialized
# ✓ Services ready
# INFO: Application startup complete [uvicorn]
# INFO: Uvicorn running on http://0.0.0.0:8000
```

#### 4. Test the API
```powershell
# In another terminal
python cli.py health

# Or use curl
curl http://localhost:8000/api/health

# Expected: {"status": "healthy", "services": {...}}
```

✅ You're ready! API docs at **http://localhost:8000/api/docs**

---

## 📱 Test the API

### 1. Simple Text Analysis

**Using the Web UI** (Easiest):
1. Go to http://localhost:8000/api/docs
2. Click "Try it out" on `/api/analyze`
3. Enter:
   ```json
   {
     "session_id": "test-1",
     "text": "The system should authenticate users quickly"
   }
   ```
4. Click "Execute"
5. See the analysis results

**Using cURL**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-1",
    "text": "The system should authenticate users quickly"
  }'
```

**Response Example**:
```json
{
  "session_id": "test-1",
  "status": "needs_clarification",
  "interrupt_needed": true,
  "clarification_questions": [
    {
      "question_id": "q1",
      "question": "What does 'quickly' mean in terms of response time (e.g., < 1s, < 500ms)?",
      "context": "Performance metric is vague",
      "required_clarity": ["response_time", "unit"]
    }
  ],
  "analysis_summary": {
    "smell_score": 0.88,
    "logical_gap_score": 0.65,
    "issues_found": 2
  }
}
```

### 2. Upload a PDF

**Using Web UI**:
1. Go to http://localhost:8000/api/docs
2. Find `/api/upload/document`
3. Click "Try it out"
4. Upload a PDF (e.g., Project Charter)
5. Get file path for context injection

**Using Python**:
```python
import requests

with open("charter.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload/document",
        files={"file": ("charter.pdf", f)}
    )
    
data = response.json()
print(f"File path: {data['file_path']}")
print(f"Sections: {data['summary']['sections']}")
```

### 3. Test Context Injection

**With PDF context**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-2",
    "text": "The system should support Chinese characters",
    "context_file_path": "/data/uploads/test-1/charter.pdf"
  }'
```

The LLM will now:
- Check if Chinese support is mentioned in the charter
- Flag if it conflicts with existing requirements
- Reference relevant sections

### 4. Test Audio Transcription

**Upload and transcribe audio file**:
```bash
curl -X POST http://localhost:8000/api/upload/audio \
  -F "file=@speech.wav"

# Response:
# {
#   "transcription": "The system should handle concurrent users efficiently",
#   "text_length": 62,
#   ...
# }
```

### 5. Export to Jira (If Configured)

**First, configure credentials** in `.env`:
```
JIRA_ENABLED=True
JIRA_SERVER_URL=https://your-jira.atlassian.net
JIRA_USERNAME=your@email.com
JIRA_API_TOKEN=your_token_here
JIRA_PROJECT_KEY=PROJ
```

**Then export**:
```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-1",
    "export_target": "jira"
  }'

# Response:
# {
#   "export_id": "uuid",
#   "target": "jira",
#   "ticket_ids": ["PROJ-123", "PROJ-124"],
#   "status": "success",
#   "url": "https://jira.com/browse/PROJ"
# }
```

---

## 🎤 Real-Time Audio Streaming

### WebSocket Test (Python)

```python
import asyncio
import websockets
import json
import base64
from pathlib import Path

async def stream_audio():
    session_id = "audio-test-1"
    
    async with websockets.connect(
        f"ws://localhost:8000/api/ws/stream/{session_id}"
    ) as ws:
        # Connection ready message
        msg = await ws.recv()
        print("Connected:", json.loads(msg))
        
        # Read audio file and stream chunks
        audio_data = Path("speech.wav").read_bytes()
        chunk_size = 3200  # ~200ms at 16kHz
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            
            await ws.send(json.dumps({
                "type": "audio_chunk",
                "data": base64.b64encode(chunk).decode(),
                "chunk_number": i // chunk_size
            }))
            
            # Check for acknowledgment
            response = await ws.recv()
            response_obj = json.loads(response)
            print(f"Chunk {response_obj['chunk_number']} ack'd")
            
            if response_obj.get("transcription"):
                print(f"Transcribed: {response_obj['transcription']}")
        
        # Finalize and get analysis
        await ws.send(json.dumps({"type": "finalize"}))
        
        # Wait for analysis complete
        while True:
            response = await ws.recv()
            response_obj = json.loads(response)
            
            if response_obj["type"] == "analysis_complete":
                print("Analysis:", response_obj["analysis"])
                break
            elif response_obj["type"] == "interrupt":
                print("Questions:", response_obj["questions"])
                break

asyncio.run(stream_audio())
```

### WebSocket Test (JavaScript)

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/api/ws/stream/js-test-1');

ws.onopen = () => {
    console.log('Connected');
    
    // Send audio chunk
    const chunk = new Uint8Array([...]);  // Your audio PCM data
    ws.send(JSON.stringify({
        type: 'audio_chunk',
        data: btoa(String.fromCharCode(...chunk)),  // base64
        chunk_number: 1
    }));
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    if (msg.type === 'chunk_ack') {
        console.log('Chunk acknowledged');
    } else if (msg.type === 'transcription') {
        console.log('Transcribed:', msg.transcription);
    } else if (msg.type === 'interrupt') {
        console.log('Need clarification:', msg.questions);
    } else if (msg.type === 'analysis_complete') {
        console.log('Done:', msg.analysis);
    }
};

// When done streaming
ws.send(JSON.stringify({ type: 'finalize' }));
```

---

## 🔧 Configuration Tips

### Optimize for Your GPU

**RTX 4070 Super** (default):
```env
WHISPER_MODEL_SIZE=base
WHISPER_COMPUTE_TYPE=float16
OLLAMA_TEMPERATURE=0.7
```

**RTX 3060 (12GB)**:
```env
WHISPER_MODEL_SIZE=base
WHISPER_COMPUTE_TYPE=float16
```

**RTX 2060 (6GB)**:
```env
WHISPER_MODEL_SIZE=tiny
WHISPER_COMPUTE_TYPE=int8
```

**No GPU (CPU only)**:
```env
WHISPER_DEVICE=cpu
# Expect 5-10x slower performance
```

### Increase Interrupt Threshold (Fewer Interrupts)
```env
SMELL_SCORE_THRESHOLD=0.85  # Default: 0.7
# Higher = less likely to interrupt
```

### Enable Jira Integration

1. Get Jira API token from https://id.atlassian.com/manage/api-tokens
2. Update `.env`:
```env
JIRA_ENABLED=True
JIRA_SERVER_URL=https://your-company.atlassian.net
JIRA_USERNAME=your@email.com
JIRA_API_TOKEN=xxxxxxxxxxxxxxxx
JIRA_PROJECT_KEY=PROJ
```
3. Restart backend

---

## 📊 Monitor Performance

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Detailed Status
```bash
curl http://localhost:8000/api/status
```

### Check Logs
```bash
# In backend terminal, or check:
cat logs/re_tool.log
```

### Monitor GPU Usage
**Terminal:**
```bash
nvidia-smi -l 1  # Refresh every 1 second
```

Watch:
- GPU Memory usage (should be ~9-10 GB for both models)
- GPU Utilization (should spike during analysis)

---

## 🐛 Common Issues

### "Ollama connection refused"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not, start it:
ollama serve
```

### "CUDA out of memory"
```
Solution 1: Reduce model size
WHISPER_MODEL_SIZE=tiny

Solution 2: Use CPU
WHISPER_DEVICE=cpu

Solution 3: Reduce float16 → int8
WHISPER_COMPUTE_TYPE=int8
```

### "WebSocket connection refused"
```
- Check FastAPI is running (python main.py)
- Check firewall allows port 8000
- Check CORS settings (should allow *)
```

### "Slow transcription"
```bash
# Check GPU is being used:
nvidia-smi  # GPU-Util should be high

- If low: GPU not enabled. Check CUDA installation
- If high but still slow: Your GPU is slower than RTX 4070 Super
```

### Model Loading Fails
```bash
# Ensure models are downloaded:
ollama pull llama3
faster_whisper  # Auto-downloads on first use

# Check disk space (need ~20GB):
disk usage
```

---

## 📚 What's Next?

### Build Frontend
- React/Flutter client
- WebSocket audio streaming
- PDF upload modal
- Clarification UI
- Export confirmation

### Extended Features
- Multi-language support
- Custom requirement templates
- Requirements versioning
- Audit trail
- Team collaboration

### Production Deployment
- Docker deployment
- Kubernetes scaling
- Redis caching
- Database persistence (PostgreSQL)
- Monitoring/alerting (Prometheus)

---

## 📖 Documentation Files

- **README.md** - Overview and API reference
- **ARCHITECTURE.md** - Deep technical details
- **This file** - Getting started guide

## 🤝 Support

For issues:
1. Check logs: `logs/re_tool.log`
2. Test API: `python cli.py health`
3. Review ARCHITECTURE.md for design details
4. Check .env configuration

Happy requirement engineering! 🚀
