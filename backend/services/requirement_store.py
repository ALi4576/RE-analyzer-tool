"""
In-memory overlay store for requirement field patches.

The LangGraph checkpointer (MemorySaver) persists the canonical requirement
documents keyed by session/thread_id. When a user edits an individual
requirement, we do not want to mutate the checkpoint directly — that would
couple editing concerns to the analysis pipeline's state graph and risk
clobbering a concurrent run. Instead, this module keeps per-session, per-
requirement field overrides that are merged on read.

Storage shape:
    { session_id: { requirement_id: { field_name: value, ... } } }

Persistence: in-memory only, consistent with the rest of the session state.
"""
from typing import Any, Dict, List


# Module-level singleton store.
# Keyed by session_id, then requirement_id, then field name.
_store: Dict[str, Dict[str, Dict[str, Any]]] = {}


def patch(session_id: str, req_id: str, fields: Dict[str, Any]) -> None:
    """
    Record field-level overrides for a single requirement within a session.

    Fields whose value is ``None`` are skipped so callers can safely pass
    ``request.dict(exclude_none=True)``-style payloads where absent fields
    should leave the overlay untouched.
    """
    if not session_id or not req_id or not fields:
        return
    _store.setdefault(session_id, {}).setdefault(req_id, {}).update(
        {k: v for k, v in fields.items() if v is not None}
    )


def get_patches(session_id: str) -> Dict[str, Dict[str, Any]]:
    """Return the full patch map for a session, or an empty dict."""
    return _store.get(session_id, {})


def merge(session_id: str, requirements: List[Dict]) -> List[Dict]:
    """
    Return a new list of requirement dicts with session overlays applied.

    The input list is not mutated. Requirements without a ``requirement_id``
    or without any recorded patch are returned unchanged.
    """
    patches = get_patches(session_id)
    if not patches:
        return requirements

    merged: List[Dict] = []
    for req in requirements:
        if not isinstance(req, dict):
            merged.append(req)
            continue
        req_id = req.get("requirement_id")
        if req_id and req_id in patches:
            # Overlay wins on conflict — that is the whole point of the store.
            merged.append({**req, **patches[req_id]})
        else:
            merged.append(req)
    return merged


class _RequirementStore:
    """Thin OO wrapper for callers that prefer an injectable instance."""

    def patch(self, session_id: str, req_id: str, fields: Dict[str, Any]) -> None:
        patch(session_id, req_id, fields)

    def merge(self, session_id: str, requirements: List[Dict]) -> List[Dict]:
        return merge(session_id, requirements)

    def get_patches(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        return get_patches(session_id)


def get_requirement_store() -> _RequirementStore:
    """Return a requirement store facade (plain object, no global state beyond the module)."""
    return _RequirementStore()
