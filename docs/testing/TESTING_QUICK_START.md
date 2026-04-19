# 🚀 QUICK START - COMPLETE BACKEND TESTING

## ⏱️ Total Time: ~10 minutes

### Step 1: Start Services (2 min)

**Terminal 1 - Ollama:**
```bash
ollama serve
```
Expected output:
```
Listening on 127.0.0.1:11434 (NNTP)
```

**Terminal 2 - Backend:**
```bash
cd f:\coding\RE_tool
python main.py
```
Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
Model preloading complete
```

**Terminal 3 - Testing:**
```bash
cd f:\coding\RE_tool
# Option A: Quick test (30 sec)
python test_backend.py

# Option B: Advanced feature tests (see TESTING_GUIDE.md)
# Option C: Manual curl/Python requests (see examples below)
```

---

## 🧪 Test Option A: Quick Test (30 seconds)

```bash
python test_backend.py
```

This tests:
1. ✅ Health check
2. ✅ System status
3. ✅ Analysis
4. ✅ Formalization
5. ✅ Export (Jira + Trello dry-run)

**Expected:** All tests pass ✅

---

## 🧪 Test Option B: Complete Features (5 minutes)

All tests from TESTING_GUIDE.md with detailed output.

See file for complete usage.

---

## 🧪 Test Option C: Manual Testing

### Test 1: Health Check
```bash
curl http://localhost:8000/api/health
```

### Test 2: Analyze Requirement
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "text": "The system should handle 1000 concurrent users with sub-500ms response times and work on mobile devices"
  }'
```

### Test 3: Get Formalized Requirements
```bash
curl -X POST "http://localhost:8000/api/formalize?session_id=test-001"
```

### Test 4: Export to Jira
```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "export_target": "jira"
  }'
```

### Test 5: Export to Trello
```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "export_target": "trello"
  }'
```

---

## 🐍 Python Testing (Recommended)

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"
SESSION_ID = "test-001"

# 1. Analyze
print("1. Analyzing requirements...")
r1 = requests.post(f"{BASE_URL}/analyze", json={
    "session_id": SESSION_ID,
    "text": "System must be fast, scalable, and mobile-friendly"
})
print(f"✅ Analyze: {r1.json()['status']}")

# 2. Formalize
print("\n2. Formalizing to ISO 29148...")
r2 = requests.post(f"{BASE_URL}/formalize", params={"session_id": SESSION_ID})
reqs = r2.json()
print(f"✅ Formalize: {len(reqs['iso_requirements'])} requirements generated")

# 3. Export to Jira
print("\n3. Exporting to Jira...")
r3 = requests.post(f"{BASE_URL}/export", json={
    "session_id": SESSION_ID,
    "export_target": "jira"
})
print(f"✅ Export: {r3.json()['status']}")

print("\n✅ All features working!")
```

---

## ✅ What Each Test Verifies

| Test | Verifies |
|------|----------|
| Health | API is running |
| Analyze | LLM integration, smell detection, state persistence |
| Formalize | ISO 29148 compliance, requirement generation |
| Export | Jira/Trello integration, data serialization |
| Dry-run | Export preview without creating tickets |

---

## 📊 Expected Results

All endpoints should return **HTTP 200** with proper JSON responses:

```json
{
  "session_id": "test-001",
  "status": "export_ready",
  "analysis_summary": {
    "smell_score": 0.35,
    "logical_gap_score": 0.42,
    "issues_found": 2
  }
}
```

---

## 🎯 Test Scenarios

### Scenario 1: Simple Requirement
```
Input: "System shall be fast"
Expected: 
- Smell score: Medium (ambiguous)
- Issues: 1-2 smells detected
- Requirements generated: 1
```

### Scenario 2: Complex Requirement
```
Input: "System shall handle 1000 concurrent users with <500ms response time, 
support mobile/web/desktop, include role-based access control, and 
encrypt all data at rest"
Expected:
- Smell score: Low (specific)
- Issues: 0-1 smell (minor)
- Requirements generated: 4-5
```

### Scenario 3: Ambiguous Requirement
```
Input: "Make the system better"
Expected:
- Smell score: High (very ambiguous)
- Issues: 3+ smells (ambiguous, incomplete, unmeasurable)
- HITL interrupt: Yes, asks clarification questions
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` | `python main.py` not running |
| `Ollama not responding` | `ollama serve` not running in Terminal 1 |
| `Empty requirements` | Analysis failed - check Ollama status |
| `Export says "failed"` | Jira/Trello credentials not configured (OK for testing) |
| `Timeout error` | First run slower (GPU warmup) - retry after 30 sec |

---

## 📚 Documentation

- **[CODE_AUDIT.md](CODE_AUDIT.md)** - Validation report (all systems GO ✅)
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Detailed feature tests
- **[test_backend.py](test_backend.py)** - Automated test script
- **[README.md](README.md)** - API documentation

---

## 🎓 What Gets Tested

✅ **Core Analysis**
- Requirement parsing
- Smell detection
- Logic analysis
- State persistence

✅ **Formalization**
- ISO 29148 compliance
- Requirement ID generation
- Acceptance criteria extraction
- Priority/category assignment

✅ **Export**
- Jira story creation
- Trello card creation
- API integration
- Graceful degradation

✅ **Advanced**
- Context injection (PDF)
- HITL clarification workflow
- Audio transcription
- Session isolation

---

## 🏁 Success Indicators

Your backend is working correctly when:

1. ✅ `python test_backend.py` shows all GREEN
2. ✅ Requirements are generated with unique IDs (REQ-0001, etc.)
3. ✅ Export endpoints return success status
4. ✅ Sessions maintain state across requests
5. ✅ No errors in logs

---

## 📞 Next Steps

After confirming everything works:

1. **Build Frontend** - Connect to WebSocket at `/api/ws/stream/{session_id}`
2. **Configure Export** - Add Jira/Trello credentials to `.env` for real integration
3. **Add Monitoring** - Set up logging aggregation, metrics collection
4. **Performance Tuning** - Optimize batch sizes, model selection for your GPU

---

## 🎉 Ready?

```bash
# 1. Terminal 1
ollama serve

# 2. Terminal 2
python main.py

# 3. Terminal 3
python test_backend.py
```

**Go!** 🚀
