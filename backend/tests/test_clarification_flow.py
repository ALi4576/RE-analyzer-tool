"""
Tests for the smell-detection → interrupt → clarification flow.

Uses unittest.mock to stub OllamaLLM.invoke so no Ollama process is required.
Tests assert:
  1. High smell score triggers interrupt with questions and status="needs_clarification"
  2. resume_after_clarification preserves original question IDs (no re-generation)
  3. After all questions are answered the pipeline does NOT re-interrupt
  4. Low smell score produces export_ready result without an interrupt
"""
import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HIGH_SMELL_RESPONSE = json.dumps([
    {"type": "ambiguous", "severity": 0.9, "location": "the system", "recommendation": "Specify the system"},
    {"type": "incomplete", "severity": 0.85, "location": "fast", "recommendation": "Define measurable threshold"},
])

LOW_SMELL_RESPONSE = json.dumps([
    {"type": "ambiguous", "severity": 0.2, "location": "some part", "recommendation": "Minor clarification"},
])

QUESTIONS_RESPONSE = json.dumps([
    {"question_id": "q1", "question": "What response time is acceptable?", "context": "performance", "required_clarity": ["latency", "SLA"]},
    {"question_id": "q2", "question": "Which systems are in scope?", "context": "scope", "required_clarity": ["systems", "boundaries"]},
])

LOGIC_ANALYSIS_RESPONSE = "gap score: 0.75"  # high gap → also triggers interrupt

FORMALIZE_RESPONSE = json.dumps([{
    "title": "System Response Time",
    "shall_statement": "The system shall respond within [Performance Constraint].",
    "rationale": "User experience depends on response time.",
    "acceptance_criteria": ["P95 latency < TBD", "Measured under load"],
    "priority": "High",
    "category": "Non-functional",
    "depends_on": [],
}])


def _make_llm_side_effect(*responses):
    """Return a side_effect list that cycles through the given responses."""
    return list(responses)


def _build_fresh_agent():
    """Instantiate a fresh RequirementsAnalysisAgent with a clean MemorySaver."""
    from core.agents import RequirementsAnalysisAgent
    return RequirementsAnalysisAgent()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent():
    """Fresh agent per test — isolated MemorySaver checkpointer."""
    return _build_fresh_agent()


@pytest.fixture
def high_smell_state():
    from models.schemas import RequirementAnalysisState
    return RequirementAnalysisState(
        session_id="test-high-smell-01",
        input_text="System should be fast and easy and scalable",
    )


@pytest.fixture
def low_smell_state():
    from models.schemas import RequirementAnalysisState
    return RequirementAnalysisState(
        session_id="test-low-smell-01",
        input_text="The authentication service shall validate user credentials within 200ms under peak load of 1000 concurrent users.",
    )


# ---------------------------------------------------------------------------
# Test: high smell → interrupt → questions emitted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_high_smell_triggers_interrupt_with_questions(agent, high_smell_state):
    """High smell score must set interrupt_needed=True and emit clarification questions."""
    llm_responses = [
        "Parsed requirement analysis",   # parse_input
        HIGH_SMELL_RESPONSE,              # detect_smells
        LOGIC_ANALYSIS_RESPONSE,          # analyze_logic
        FORMALIZE_RESPONSE,               # formalize
        QUESTIONS_RESPONSE,               # generate_questions
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        result = await agent.analyze(high_smell_state)

    assert result["interrupt_needed"] is True, "Expected interrupt_needed=True for high smell"
    assert result["status"] == "needs_clarification", f"Unexpected status: {result['status']}"

    questions = result.get("clarification_questions") or []
    assert len(questions) >= 1, "Expected at least one clarification question"

    ids = {q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None) for q in questions}
    assert None not in ids, "All questions must have a question_id"


# ---------------------------------------------------------------------------
# Test: resume preserves question IDs, does not re-generate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resume_preserves_question_ids(agent, high_smell_state):
    """After resume, question IDs must match the interrupted run — no regeneration."""
    llm_responses_first = [
        "Parsed analysis",
        HIGH_SMELL_RESPONSE,
        LOGIC_ANALYSIS_RESPONSE,
        FORMALIZE_RESPONSE,
        QUESTIONS_RESPONSE,
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses_first), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        first_result = await agent.analyze(high_smell_state)

    first_ids = {
        q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None)
        for q in (first_result.get("clarification_questions") or [])
    }
    assert first_ids, "First run must produce questions"

    # Resume with answers keyed by the ORIGINAL IDs
    clarifications = {qid: f"Answer for {qid}" for qid in first_ids}

    llm_responses_resume = [
        "Parsed analysis",       # parse_input on resume
        HIGH_SMELL_RESPONSE,     # detect_smells (smell still high — loop-breaker must suppress re-interrupt)
        LOGIC_ANALYSIS_RESPONSE, # analyze_logic
        FORMALIZE_RESPONSE,      # formalize
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses_resume), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        resume_result = await agent.resume_after_clarification(
            high_smell_state.session_id, clarifications
        )

    resumed_ids = {
        q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None)
        for q in (resume_result.get("clarification_questions") or [])
    }

    assert first_ids == resumed_ids or not resumed_ids, (
        f"Resume changed question IDs: {first_ids} → {resumed_ids}"
    )


# ---------------------------------------------------------------------------
# Test: no re-interrupt once all questions are answered
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_re_interrupt_after_all_answers(agent, high_smell_state):
    """Pipeline must not interrupt again when the user has answered all prior questions."""
    llm_responses_first = [
        "Parsed analysis",
        HIGH_SMELL_RESPONSE,
        LOGIC_ANALYSIS_RESPONSE,
        FORMALIZE_RESPONSE,
        QUESTIONS_RESPONSE,
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses_first), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        first_result = await agent.analyze(high_smell_state)

    question_ids = {
        q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None)
        for q in (first_result.get("clarification_questions") or [])
    }
    full_clarifications = {qid: "User provided answer." for qid in question_ids}

    # Smell stays high on resume — loop-breaker in _should_interrupt must fire
    llm_responses_resume = [
        "Parsed analysis",
        HIGH_SMELL_RESPONSE,
        LOGIC_ANALYSIS_RESPONSE,
        FORMALIZE_RESPONSE,
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses_resume), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        resume_result = await agent.resume_after_clarification(
            high_smell_state.session_id, full_clarifications
        )

    assert resume_result.get("interrupt_needed") is False, (
        "Pipeline must not re-interrupt when all prior questions are answered"
    )
    assert resume_result.get("status") in ("export_ready", "formal_draft", "clarified"), (
        f"Expected a terminal status after full clarification, got: {resume_result.get('status')}"
    )


# ---------------------------------------------------------------------------
# Test: low smell → no interrupt, export_ready
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_low_smell_no_interrupt(agent, low_smell_state):
    """Low smell score must NOT trigger interrupt and must reach export_ready."""
    low_logic = "consistency: 0.9"  # high consistency → low gap
    llm_responses = [
        "Parsed analysis",
        LOW_SMELL_RESPONSE,
        low_logic,
        FORMALIZE_RESPONSE,
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        result = await agent.analyze(low_smell_state)

    assert result.get("interrupt_needed") is False, (
        "Low smell should not trigger interrupt"
    )
    assert result.get("status") == "export_ready", (
        f"Expected export_ready, got: {result.get('status')}"
    )
    assert len(result.get("requirements", [])) > 0, "Expected requirements in output"


# ---------------------------------------------------------------------------
# Test: fallback question generated when LLM returns garbage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_question_on_malformed_llm_output(agent, high_smell_state):
    """When LLM returns non-JSON for questions, a fallback question must be emitted."""
    llm_responses = [
        "Parsed analysis",
        HIGH_SMELL_RESPONSE,
        LOGIC_ANALYSIS_RESPONSE,
        FORMALIZE_RESPONSE,
        "I cannot generate questions for this input.",  # malformed — not JSON
    ]

    with patch.object(agent.llm, "invoke", side_effect=llm_responses), \
         patch.object(agent.formalize_llm, "invoke", return_value=FORMALIZE_RESPONSE):
        result = await agent.analyze(high_smell_state)

    questions = result.get("clarification_questions") or []
    assert len(questions) >= 1, "Fallback question must be emitted on malformed LLM output"
    assert result.get("interrupt_needed") is True
    assert result.get("status") == "needs_clarification"
