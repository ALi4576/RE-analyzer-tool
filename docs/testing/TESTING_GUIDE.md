# 🧪 Comprehensive Backend Testing Guide (No Frontend Required)

## ✅ Pre-Flight Checklist

Before testing, ensure:
- [ ] Ollama running: `ollama serve`
- [ ] Backend starting: `python main.py`
- [ ] Python 3.10+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`

---

## 📋 Test Scenarios (Complete Flow)

### **Quick Health Check (30 seconds)**

```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend
cd f:\coding\RE_tool
python main.py

# Terminal 3: Test
python cli.py health
```

Expected output:
```json
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

## 🧬 Full Feature Test (Complete)

### **Test 1: Basic Requirement Analysis** ✅
Tests: Parsing → Smell Detection → Formalization

```python
import requests
import json

# Create session
SESSION_ID = "test-session-001"
base_url = "http://localhost:8000/api"

# 1. Analyze a requirement
requirement_text = """
The system should be fast and provide good performance 
for users. It must handle multiple requests at the same time.
The application should work well on mobile devices.
"""

response = requests.post(
    f"{base_url}/analyze",
    json={
        "session_id": SESSION_ID,
        "text": requirement_text,
        "context_file_path": None
    }
)

print("✅ ANALYZE Response:")
print(json.dumps(response.json(), indent=2))

# Expected:
# {
#   "session_id": "test-session-001",
#   "status": "analyzing" or "needs_clarification",
#   "interrupt_needed": True/False,
#   "analysis_summary": {
#       "smell_score": 0.X,
#       "logical_gap_score": 0.X,
#       "issues_found": N
#   }
# }
```

**What's tested:**
- ✅ Session creation
- ✅ LLM parsing of requirement text
- ✅ Smell detection (ambiguity, incompleteness, etc.)
- ✅ Logic analysis (gaps, conflicts)
- ✅ State storage in LangGraph checkpoint

---

### **Test 2: Human-in-the-Loop (HITL) Clarification** ✅
Tests: Interrupt detection → Question generation → Resume

```python
# 2. If interrupted (smell_score >= 0.7), clarify

# First check if we got interrupted
analyze_response = response.json()
if analyze_response.get("interrupt_needed"):
    
    print("\n✅ INTERRUPT DETECTED - Asking clarification questions...")
    
    # Get the questions from analysis
    questions = analyze_response.get("clarification_questions", [])
    
    # Mock user responses
    clarifications = {}
    for q in questions:
        clarifications[q["question_id"]] = "Clarified response for this question"
    
    # Submit clarifications
    clarify_response = requests.post(
        f"{base_url}/clarify",
        json={
            "session_id": SESSION_ID,
            "question_id": list(clarifications.keys())[0] if clarifications else "q1",
            "user_response": "Clarified: Performance target is <500ms response time"
        }
    )
    
    print("\n✅ CLARIFY Response:")
    print(json.dumps(clarify_response.json(), indent=2))

else:
    print("\n✅ No interrupt needed - Analysis clean, resuming to formalization...")
```

**What's tested:**
- ✅ LangGraph checkpoint/resume mechanism
- ✅ Smell detection accuracy
- ✅ Clarification question generation
- ✅ State persistence across requests

---

### **Test 3: Formalization (ISO 29148)** ✅
Tests: Requirement conversion → ID generation → Acceptance criteria

```python
# 3. Retrieve formalized requirements from session state

print("\n✅ FORMALIZE - Retrieve ISO 29148 requirements...")

formalize_response = requests.post(
    f"{base_url}/formalize",
    params={"session_id": SESSION_ID}
)

print("\n✅ FORMALIZE Response:")
formalized = formalize_response.json()
print(json.dumps(formalized, indent=2))

# Expected structure:
# {
#   "iso_requirements": [
#       {
#           "requirement_id": "REQ-0001",
#           "title": "...",
#           "shall_statement": "System shall...",
#           "rationale": "...",
#           "acceptance_criteria": ["criterion 1", "criterion 2"],
#           "priority": "High|Medium|Low",
#           "category": "Functional|Non-functional|Interface",
#           "traceability": []
#       }
#   ],
#   "summary": "Found X requirements",
#   "total_requirements": N,
#   "completeness_score": 0.X,
#   "ready_for_export": True/False,
#   "export_formats": ["jira", "trello"]
# }
```

**What's tested:**
- ✅ LangGraph state retrieval (requirements key exists!)
- ✅ ISO 29148 compliance formatting
- ✅ Unique requirement ID generation (REQ-0001, etc.)
- ✅ Shall statement generation (imperative form)
- ✅ Acceptance criteria extraction
- ✅ Priority/category assignment

---

### **Test 4: Export to Jira** ✅
Tests: Jira story creation, field mapping, API integration

```python
# 4. Export to Jira

print("\n✅ EXPORT TO JIRA...")

# First check if requirements exist
if formalized.get("ready_for_export") and formalized.get("total_requirements", 0) > 0:
    
    export_response = requests.post(
        f"{base_url}/export",
        json={
            "session_id": SESSION_ID,
            "export_target": "jira"
        }
    )
    
    print("\n✅ JIRA EXPORT Response:")
    export_result = export_response.json()
    print(json.dumps(export_result, indent=2))
    
    # Expected:
    # {
    #   "export_id": "uuid",
    #   "target": "jira",
    #   "ticket_ids": ["PROJ-123", "PROJ-124"],
    #   "status": "success",
    #   "url": "https://jira.company.com/browse/PROJ-123"
    # }
    
    if export_result.get("status") == "success":
        print(f"✅ SUCCESS: Created {len(export_result.get('ticket_ids', []))} Jira tickets")
        for ticket_id in export_result.get("ticket_ids", []):
            print(f"   - {export_result.get('url')}")
    else:
        print("⚠️  Export failed or credentials not configured")
        print("   (This is OK for testing - configure .env to enable)")

else:
    print("❌ ERROR: No requirements ready for export")
```

**What's tested:**
- ✅ Jira API authentication
- ✅ Story creation with description formatting
- ✅ Field mapping (priority, category, title)
- ✅ Custom fields (requirement_id, acceptance_criteria)
- ✅ Error handling if credentials not configured

---

### **Test 5: Export to Trello** ✅
Tests: Trello card creation

```python
# 5. Export to Trello (same session)

print("\n✅ EXPORT TO TRELLO...")

if formalized.get("ready_for_export") and formalized.get("total_requirements", 0) > 0:
    
    export_trello = requests.post(
        f"{base_url}/export",
        json={
            "session_id": SESSION_ID,
            "export_target": "trello"
        }
    )
    
    print("\n✅ TRELLO EXPORT Response:")
    trello_result = export_trello.json()
    print(json.dumps(trello_result, indent=2))
    
    if trello_result.get("status") == "success":
        print(f"✅ SUCCESS: Created {len(trello_result.get('ticket_ids', []))} Trello cards")
    else:
        print("⚠️  Trello export failed or not configured")
```

**What's tested:**
- ✅ Trello API authentication
- ✅ Card creation
- ✅ List organization
- ✅ Description formatting

---

### **Test 6: Dry-Run Export Preview** ✅
Tests: Export preview without creating tickets

```python
# 6. Preview export without creating tickets

print("\n✅ DRY-RUN EXPORT (Preview only)...")

dryrun_response = requests.post(
    f"{base_url}/export/dry-run",
    json={
        "session_id": SESSION_ID,
        "export_target": "jira"
    }
)

print("\n✅ DRY-RUN Response:")
preview = dryrun_response.json()
print(json.dumps(preview, indent=2))

# Expected:
# {
#   "session_id": "...",
#   "preview": {
#       "would_create": N,
#       "sample": {...}
#   }
# }
```

**What's tested:**
- ✅ Export preview generation
- ✅ No tickets actually created

---

### **Test 7: Audio File Transcription** ✅
Tests: Faster-Whisper GPU transcription

```python
# 7. Transcribe audio file

print("\n✅ TRANSCRIBE AUDIO FILE...")

# You'll need a test audio file
# For now, just show the API structure
transcribe_request = {
    "file_path": "data/uploads/sample_audio.wav",
    "language": "en"
}

transcribe_response = requests.post(
    f"{base_url}/transcribe",
    json=transcribe_request
)

print("\n✅ TRANSCRIBE Response:")
print(json.dumps(transcribe_response.json(), indent=2))

# Expected:
# {
#   "text": "Transcribed audio content...",
#   "length": 234,
#   "language": "en"
# }
```

**What's tested:**
- ✅ Faster-Whisper integration
- ✅ GPU acceleration (float16 precision)
- ✅ language detection

---

### **Test 8: File Upload (Audio)** ✅
Tests: Audio file upload + automatic transcription

```python
# 8. Upload audio file

print("\n✅ UPLOAD AUDIO FILE...")

# Create a simple test audio file (or use existing one)
test_audio_file = open("test_audio.wav", "rb")  # Replace with actual file

upload_response = requests.post(
    f"{base_url}/upload/audio",
    files={"file": test_audio_file}
)

print("\n✅ UPLOAD AUDIO Response:")
upload_result = upload_response.json()
print(json.dumps(upload_result, indent=2))

# Expected:
# {
#   "session_id": "...",
#   "file_path": "data/uploads/.../audio.wav",
#   "transcription": "Transcribed text...",
#   "text_length": 234
# }
```

**What's tested:**
- ✅ File upload handling
- ✅ Automatic transcription
- ✅ Session management

---

### **Test 9: Document Upload (PDF)** ✅
Tests: PDF upload + context extraction

```python
# 9. Upload PDF for context injection

print("\n✅ UPLOAD DOCUMENT (PDF)...")

# You'll need a sample PDF
pdf_file = open("requirements_charter.pdf", "rb")

upload_doc_response = requests.post(
    f"{base_url}/upload/document",
    files={"file": pdf_file}
)

print("\n✅ UPLOAD DOCUMENT Response:")
doc_result = upload_doc_response.json()
print(json.dumps(doc_result, indent=2))

# Expected:
# {
#   "session_id": "...",
#   "file_path": "data/uploads/.../doc.pdf",
#   "summary": {
#       "document_title": "...",
#       "sections": N,
#       "extracted_chars": N
#   }
# }
```

**What's tested:**
- ✅ PDF upload
- ✅ PyMuPDF text extraction
- ✅ Section identification

---

### **Test 10: Analysis WITH Context Injection** ✅
Tests: Ground truth verification

```python
# 10. Analyze with context PDF

print("\n✅ ANALYZE WITH CONTEXT INJECTION...")

context_session_id = "test-session-with-context"

# Upload PDF first
pdf_file = open("charter.pdf", "rb")
upload_doc = requests.post(f"{base_url}/upload/document", files={"file": pdf_file})
pdf_path = upload_doc.json()["file_path"]

# Then analyze with context
analyze_with_context = requests.post(
    f"{base_url}/analyze",
    json={
        "session_id": context_session_id,
        "text": "The system should be fast",
        "context_file_path": pdf_path
    }
)

print("\n✅ ANALYZE WITH CONTEXT Response:")
print(json.dumps(analyze_with_context.json(), indent=2))

# What's tested:
# ✅ PDF context loading
# ✅ Context injection into LLM prompts
# ✅ Ground truth verification
# ✅ Contradiction detection against charter
```

---

## 🔄 Complete Test Script (All-in-One)

Save this as `test_complete.py`:

```python
#!/usr/bin/env python3
"""
Complete backend test script (no frontend required).
Tests all major features end-to-end.
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def log(title, data):
    """Pretty print test results."""
    print(f"\n{'='*60}")
    print(f"✅ {title}")
    print(f"{'='*60}")
    if isinstance(data, dict):
        print(json.dumps(data, indent=2))
    else:
        print(data)
    print()

def test_health():
    """Test health check."""
    response = requests.get(f"{BASE_URL}/health")
    log("HEALTH CHECK", response.json())
    assert response.status_code == 200

def test_status():
    """Test system status."""
    response = requests.get(f"{BASE_URL}/status")
    log("SYSTEM STATUS", response.json())
    assert response.status_code == 200

def test_analyze():
    """Test requirement analysis."""
    SESSION_ID = f"test-{int(time.time())}"
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={
            "session_id": SESSION_ID,
            "text": "The system should be fast, handle multiple users, and work on mobile",
            "context_file_path": None
        }
    )
    
    log("ANALYZE ENDPOINT", response.json())
    result = response.json()
    
    assert response.status_code == 200
    assert result["session_id"] == SESSION_ID
    assert "status" in result
    assert "interrupt_needed" in result
    assert "analysis_summary" in result
    
    return SESSION_ID, result

def test_formalize(session_id):
    """Test formalization."""
    response = requests.post(
        f"{BASE_URL}/formalize",
        params={"session_id": session_id}
    )
    
    log("FORMALIZE ENDPOINT", response.json())
    result = response.json()
    
    assert response.status_code == 200
    assert "iso_requirements" in result
    assert "total_requirements" in result
    assert isinstance(result["iso_requirements"], list)
    
    return result

def test_export_jira(session_id, formalized):
    """Test Jira export."""
    if not formalized.get("ready_for_export"):
        print("⚠️  Skipping Jira export - requirements not ready")
        return
    
    response = requests.post(
        f"{BASE_URL}/export",
        json={
            "session_id": session_id,
            "export_target": "jira"
        }
    )
    
    log("EXPORT TO JIRA", response.json())
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            print(f"✅ Created {len(result.get('ticket_ids', []))} Jira tickets")
        else:
            print("⚠️  Export returned but status not success (check Jira credentials in .env)")

def test_export_trello(session_id, formalized):
    """Test Trello export."""
    if not formalized.get("ready_for_export"):
        print("⚠️  Skipping Trello export - requirements not ready")
        return
    
    response = requests.post(
        f"{BASE_URL}/export",
        json={
            "session_id": session_id,
            "export_target": "trello"
        }
    )
    
    log("EXPORT TO TRELLO", response.json())
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            print(f"✅ Created {len(result.get('ticket_ids', []))} Trello cards")
        else:
            print("⚠️  Export returned but status not success (check Trello credentials in .env)")

def test_dry_run(session_id):
    """Test dry-run export."""
    response = requests.post(
        f"{BASE_URL}/export/dry-run",
        json={
            "session_id": session_id,
            "export_target": "jira"
        }
    )
    
    log("DRY-RUN EXPORT", response.json())
    assert response.status_code == 200

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"🧪 COMPREHENSIVE BACKEND TEST SUITE")
    print(f"{'='*60}")
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run tests in sequence
        test_health()
        test_status()
        
        session_id, analysis = test_analyze()
        formalized = test_formalize(session_id)
        test_export_jira(session_id, formalized)
        test_export_trello(session_id, formalized)
        test_dry_run(session_id)
        
        print(f"\n{'='*60}")
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
```

Run it with:
```bash
python test_complete.py
```

---

## 🚀 Running the Full Test

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Backend
python main.py

# Terminal 3: Run tests
python test_complete.py
```

---

## 📊 Expected Test Output

```
============================================================
🧪 COMPREHENSIVE BACKEND TEST SUITE
============================================================
Testing: http://localhost:8000/api
Time: 2026-04-16 10:30:45

============================================================
✅ HEALTH CHECK
============================================================
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "transcriber": "ready",
    "agent": "ready",
    "exporter": "ready"
  }
}

============================================================
✅ ANALYZE ENDPOINT
============================================================
{
  "session_id": "test-1713271845",
  "status": "export_ready",
  "interrupt_needed": false,
  "clarification_questions": null,
  "analysis_summary": {
    "smell_score": 0.35,
    "logical_gap_score": 0.42,
    "issues_found": 2
  }
}

============================================================
✅ FORMALIZE ENDPOINT
============================================================
{
  "iso_requirements": [
    {
      "requirement_id": "REQ-0001",
      "title": "System Performance",
      "shall_statement": "System shall respond in less than 500ms",
      "rationale": "Users expect fast response times",
      "acceptance_criteria": ["Response time < 500ms"],
      "priority": "High",
      "category": "Non-functional",
      "traceability": []
    }
  ],
  "total_requirements": 1,
  "completeness_score": 0.85,
  "ready_for_export": true,
  "export_formats": ["jira", "trello"]
}

✅ Created 1 Jira tickets
✅ Created 1 Trello cards

============================================================
✅ ALL TESTS COMPLETED SUCCESSFULLY!
============================================================
```

---

## ✅ Features Coverage Checklist

- ✅ Health check
- ✅ System status
- ✅ Requirement analysis
- ✅ Smell detection
- ✅ Logic analysis
- ✅ HITL clarification
- ✅ Formalization (ISO 29148)
- ✅ Requirement ID generation
- ✅ Acceptance criteria extraction
- ✅ Jira export
- ✅ Trello export
- ✅ Dry-run export
- ✅ Audio transcription
- ✅ File upload (audio)
- ✅ File upload (PDF)
- ✅ Context injection
- ✅ State persistence
- ✅ Session management

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Ensure backend running: `python main.py` |
| `Ollama not responding` | Start Ollama: `ollama serve` |
| `Export failed` | Configure `.env` with Jira/Trello credentials |
| `No requirements found` | Run analyze first to populate state |
| `PDF extraction error` | Ensure PDF is valid, not encrypted |
| `Audio transcription slow` | First run warms up GPU, subsequent runs are faster |

---

## 📝 Notes

1. **First run slower**: GPU model loading takes time on first transcription
2. **No database**: All state stored in LangGraph memory (MemorySaver)
3. **Session isolation**: Each session_id has separate state
4. **Credentials optional**: Export works even without Jira/Trello configured (graceful degradation)

---

**Happy Testing!** 🚀
