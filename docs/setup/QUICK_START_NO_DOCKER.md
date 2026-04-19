# ⚡ Quick Start (No Docker)

## Prerequisites
- Python 3.10+
- CUDA toolkit (for RTX GPU)
- Ollama installed

## Step 1: Setup (5 min)

```bash
cd f:\coding\RE_tool
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Step 2: Start Ollama (Terminal 1)

```bash
ollama serve
```

Wait for:
```
Listening on 127.0.0.1:11434
```

## Step 3: Start Backend (Terminal 2)

```bash
cd f:\coding\RE_tool
venv\Scripts\activate
python main.py
```

Wait for:
```
Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Run Tests (Terminal 3)

```bash
cd f:\coding\RE_tool
venv\Scripts\activate
python test_backend.py
```

## Expected Output

```
✅ Health Check
✅ System Status
✅ Analyze Requirements
✅ Formalize Requirements
✅ Jira Dry-Run Export
✅ Trello Dry-Run Export

✅ ALL TESTS COMPLETED!
```

## Manual Test (Optional)

```bash
# In Terminal 3, run:
python -c "
import requests, json
r = requests.post('http://localhost:8000/api/analyze', json={
    'session_id': 'test-001',
    'text': 'System shall handle 1000 users concurrently'
})
print(json.dumps(r.json(), indent=2))
"
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| Connection refused | Backend not running (Terminal 2) |
| Ollama not responding | Start Ollama (Terminal 1) |
| venv not found | Run: `python -m venv venv` |
| Import errors | Run: `pip install -r requirements.txt` |

## Done ✅

- **Health:** http://localhost:8000/api/health
- **Docs:** http://localhost:8000/api/docs
- **WebSocket:** ws://localhost:8000/api/ws/stream/SESSION_ID

Full test guide: See `TESTING_GUIDE.md`
