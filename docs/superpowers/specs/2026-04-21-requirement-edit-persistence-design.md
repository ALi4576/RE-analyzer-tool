# Requirement Edit Persistence & Single-Requirement Clarify

**Date:** 2026-04-21  
**Status:** Approved

---

## Problem

Requirement edits made in the frontend live only in Zustand (browser memory) — they are lost on page refresh and never reach exports. Additionally, clicking "Clarify" on a single requirement re-runs the full AI pipeline, replacing all cards.

---

## Goals

1. PATCH endpoint persists requirement edits server-side for the session lifetime
2. `/formalize`, `/export`, and `/export/pdf` reflect edited requirements
3. POST clarify endpoint re-analyzes a single requirement without touching others

---

## Non-Goals

- Persistence across server restarts (consistent with existing MemorySaver behavior)
- Database storage
- Multi-user conflict resolution

---

## Architecture

### Overlay Store (`backend/services/requirement_store.py`)

A module-level dict — `Dict[session_id, Dict[req_id, Dict[field, value]]]` — holds patches on top of LangGraph state. Three functions:

- `patch(session_id, req_id, fields)` — upserts field-level changes
- `get_patches(session_id)` — returns all patches for a session
- `merge(session_id, requirements)` — applies stored patches over a raw requirements list, returning the merged result

A `get_requirement_store()` singleton getter mirrors the existing `get_agent()` pattern.

### New Endpoints (`backend/api/routes.py`)

**PATCH `/api/requirements/{session_id}/{requirement_id}`**
- Body: `{ title?, shall_statement?, rationale?, acceptance_criteria?, priority? }`
- Validates the session exists in LangGraph state (404 if not)
- Writes to overlay store via `patch()`
- Returns the full merged requirement

**POST `/api/requirements/{session_id}/{requirement_id}/clarify`**
- Body: `{ additional_context: string }`
- Fetches the current (merged) requirement from LangGraph state + overlay
- Calls a lightweight LLM prompt to improve just that requirement
- Writes improved fields back to the overlay store via `patch()`
- Returns `{ iso_requirements: [ISORequirement] }` — only the updated requirement

### Updated Read Paths

`/formalize`, `/export`, `/export/pdf` — all currently read raw requirements from `agent.app.get_state(config)`. Each will call `store.merge(session_id, raw_requirements)` before building the response. No other logic changes.

### New Pydantic Models (`backend/models/schemas.py`)

```python
class PatchRequirementRequest(BaseModel):
    title: Optional[str] = None
    shall_statement: Optional[str] = None
    rationale: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    priority: Optional[str] = None

class ClarifyRequirementRequest(BaseModel):
    additional_context: str
```

---

## Data Flow

```
Frontend PATCH edit
  → PATCH /api/requirements/{session}/{req_id}
  → overlay_store.patch(session_id, req_id, fields)
  → returns merged ISORequirement

Frontend clicks Export
  → /export or /export/pdf
  → agent.app.get_state() → raw_requirements
  → overlay_store.merge(session_id, raw_requirements)   ← edits applied here
  → export proceeds with merged list

Frontend clicks Clarify on one card
  → POST /api/requirements/{session}/{req_id}/clarify
  → fetch current merged req
  → single LLM call to improve fields
  → overlay_store.patch(session_id, req_id, improved_fields)
  → returns updated ISORequirement only
```

---

## Error Handling

- PATCH/clarify on unknown session_id → 404
- PATCH with no valid fields → 422 (Pydantic validation)
- LLM failure in single-req clarify → 500 with descriptive message; overlay unchanged
- Overlay store is process-scoped; lost on restart (expected, documented)

---

## Testing

- Unit: `merge()` correctly applies patches, partial patches don't wipe untouched fields
- Integration: PATCH → `/formalize` round-trip returns edited values
- Integration: `/clarify` on one req doesn't affect other reqs in the session
- Edge: PATCH on session that has no LangGraph state → 404

---

## Files Changed

| File | Change |
|---|---|
| `backend/services/requirement_store.py` | New — overlay store |
| `backend/services/__init__.py` | Export `get_requirement_store` |
| `backend/models/schemas.py` | Add `PatchRequirementRequest`, `ClarifyRequirementRequest` |
| `backend/api/routes.py` | Add PATCH + POST/clarify endpoints; update formalize/export/pdf to merge |
