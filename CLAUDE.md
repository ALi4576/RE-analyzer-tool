## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
- PREFER_GRAPH: Always query graphify-out/graph.json before using `grep` or `ls`.
- SCOPE_LIMIT: If a query can be answered by graphify-out/wiki/index.md, do NOT read source files.
- AUDIO_IGNORE: Never attempt to read or summarize binary media files; refer only to graphify-extracted transcripts.

# Project: RE_tool (Requirements Engineering)

## 📊 Knowledge Graph & Context Management
This project uses **Graphify** to minimize token waste.
- **Rules**:
  - Before reading source code, browse `graphify-out/wiki/index.md` or read `graphify-out/GRAPH_REPORT.md` for God Nodes.
  - **PREFER_GRAPH**: Always query `graphify-out/graph.json` before using `grep` or `ls`.
  - **SCOPE_LIMIT**: If a query is answerable by the wiki, DO NOT read raw source files.
  - **AUDIO_IGNORE**: Never attempt to read binary media files (`*.webm`, `*.wav`); refer strictly to transcripts.

## 🛠️ Development Workflow
- **Documentation First**: For non-coding problems or planning, navigate `docs/` and `graphify-out/wiki/` first.
- **Plan-Before-Code**:
  1. Research state via Graphify/Docs.
  2. Propose a technical plan (e.g., LangGraph node structure).
  3. **STOP** and wait for user confirmation before writing code.
- **Token Hygiene**:
  - Run `/compact` after every successfully completed sub-task.
  - If a session hits >30k input tokens, suggest a session restart.

## 📋 Core Engineering Standards
- **ISO 29148 Compliance**: All formalized requirements must include ID, "Shall" statement, and measurable acceptance criteria.
- **LangGraph State**: Keep state objects lean. Use a "State Compressor" node to summarize transcripts every 5 nodes.
- **Backend**: FastAPI (Async/Await).
- **Transcription**: `faster-whisper` (Compute: `float16`).

## ⌨️ Common Commands
- **Sync Graph**: `graphify update .` (AST-only, $0 cost).
- **Watch Mode**: `graphify --watch .` (Keep in separate terminal).
- **Check Budget**: `/stats` or `/cost`.
- **Test Suite**: `pytest src/tests`.

---
*Note: If the codebase appears to differ from the Graphify wiki, notify the user immediately.*