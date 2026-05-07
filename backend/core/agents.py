"""
Multi-Agent Orchestration using LangGraph.
Implements the "Squad" logic with Human-in-the-Loop pattern for requirements analysis.
"""
import asyncio
from typing import Dict, Any, List, Optional, TypedDict, Literal
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from config import settings
from models.schemas import (
    ISORequirement,
    RequirementAnalysisState,
    RequirementSmellAnalysis,
    RequirementSmell,
    ClarificationQuestion,
    AnalysisStatus,
)
from core.context_manager import get_context_manager
from core.formalize import get_formalizer
from utils import get_logger

logger = get_logger("agent")


# ============ LLM Factory ============
def _build_llm(
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool = True,
):
    """Construct a LangChain LLM/ChatModel for the given provider.

    Lazy-imports provider packages so a missing optional dependency only
    raises when that provider is actually selected. Raises ValueError early
    (at agent init) if a cloud provider is selected without its API key.

    Args:
        provider: One of "ollama", "openai", "anthropic", "gemini".
        model:    Provider-specific model identifier (e.g. "llama3",
                  "gpt-4o-mini", "claude-3-5-sonnet-latest", "gemini-1.5-pro").
        temperature: Sampling temperature.
        max_tokens:  Upper bound on generated tokens.
        json_mode:   Request a JSON-object response when supported by the
                     provider. Anthropic does not expose this knob, so it is
                     silently ignored there.

    Returns:
        A LangChain Runnable supporting `.invoke(prompt) -> str | message`.
    """
    provider = (provider or "ollama").lower().strip()

    if provider == "ollama":
        kwargs: Dict[str, Any] = {
            "base_url": settings.OLLAMA_BASE_URL,
            "model": model or settings.OLLAMA_MODEL,
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        if json_mode:
            kwargs["format"] = "json"
        return OllamaLLM(**kwargs)

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "LLM provider 'openai' selected but OPENAI_API_KEY is not set."
            )
        from langchain_openai import ChatOpenAI  # lazy import

        kwargs = {
            "model": model or "gpt-4o-mini",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": settings.OPENAI_API_KEY,
        }
        if settings.OPENAI_API_BASE:
            kwargs["base_url"] = settings.OPENAI_API_BASE
        if json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
        return ChatOpenAI(**kwargs)

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "LLM provider 'anthropic' selected but ANTHROPIC_API_KEY is not set."
            )
        from langchain_anthropic import ChatAnthropic  # lazy import

        # Anthropic does not expose response_format=json_object; rely on
        # prompt-level JSON instructions (already used throughout the agent).
        return ChatAnthropic(
            model=model or "claude-3-5-sonnet-latest",
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.ANTHROPIC_API_KEY,
        )

    if provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "LLM provider 'gemini' selected but GOOGLE_API_KEY is not set."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI  # lazy import

        kwargs = {
            "model": model or "gemini-1.5-pro",
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "google_api_key": settings.GOOGLE_API_KEY,
        }
        if json_mode:
            # google-genai accepts MIME-type response shaping
            kwargs["response_mime_type"] = "application/json"
        return ChatGoogleGenerativeAI(**kwargs)

    raise ValueError(
        f"Unsupported LLM provider '{provider}'. "
        f"Expected one of: {settings.SUPPORTED_LLM_PROVIDERS}."
    )


def _resolve_role(role_provider: str, role_model: str) -> tuple[str, str]:
    """Resolve a per-role (provider, model) pair with fallback rules.

    - Empty role_provider inherits the main LLM_PROVIDER.
    - When the resolved provider is 'ollama' and role_model is empty,
      fall back to OLLAMA_MODEL for backward compatibility.
    - For non-ollama providers, an empty role_model lets the factory pick
      a sensible default (see _build_llm).
    """
    provider = (role_provider or settings.LLM_PROVIDER or "ollama").lower()
    model = role_model or ""
    if provider == "ollama" and not model:
        model = settings.OLLAMA_MODEL
    return provider, model


# ============ LangGraph State Schema ============
class AgentState(TypedDict, total=False):
    """LangGraph state schema for requirement analysis workflow."""
    session_id: str
    input_text: str
    context_docs: List[Dict[str, Any]]
    parsed_analysis: str
    smells: List[Dict[str, Any]]
    smell_score: float
    logical_gap_score: float
    logic_analysis: str
    clarification_questions: List[Dict[str, Any]]
    requirements: List[Dict[str, Any]]
    status: str
    interrupt_needed: bool
    formalized: Dict[str, Any]
    user_clarifications: Dict[str, str]
    # Counter for iterative clarification rounds. Starts at 0; incremented each
    # time _generate_questions_node emits a fresh batch of questions. Capped by
    # settings.MAX_CLARIFICATION_ROUNDS to prevent infinite loops.
    clarification_round: int


class RequirementsAnalysisAgent:
    """
    Multi-agent system for analyzing requirements.
    
    Agent Squad:
    1. Parser Agent: Extracts intent and entities
    2. Smell Detector: Identifies requirement smells
    3. Logical Analyzer: Finds gaps and conflicts
    4. Clarifier: Generates clarification questions
    5. Formalizer: Creates ISO 29148 output
    """
    
    def __init__(self):
        """Initialize agent squad with LangGraph."""
        # ---- Analysis LLM (smell detection + gap scoring) ----
        # Provider falls back to LLM_PROVIDER, which defaults to 'ollama'.
        # When running on ollama, the model falls back through:
        #   ANALYSIS_LLM_MODEL -> OLLAMA_ANALYSIS_MODEL -> OLLAMA_MODEL.
        analysis_provider, analysis_model = _resolve_role(
            settings.ANALYSIS_LLM_PROVIDER,
            settings.ANALYSIS_LLM_MODEL or (
                settings.OLLAMA_ANALYSIS_MODEL if (settings.ANALYSIS_LLM_PROVIDER or settings.LLM_PROVIDER) == "ollama" else ""
            ),
        )
        self.analysis_llm = _build_llm(
            provider=analysis_provider,
            model=analysis_model,
            temperature=settings.OLLAMA_ANALYSIS_TEMPERATURE,
            max_tokens=settings.OLLAMA_ANALYSIS_NUM_PREDICT,
            json_mode=True,
        )

        # ---- Main LLM (clarification question generation) ----
        main_provider, main_model = _resolve_role(
            settings.LLM_PROVIDER,
            settings.LLM_MODEL or (settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else ""),
        )
        self.llm = _build_llm(
            provider=main_provider,
            model=main_model,
            temperature=settings.OLLAMA_TEMPERATURE,
            max_tokens=settings.OLLAMA_NUM_PREDICT,
            json_mode=True,
        )

        # ---- Formalize LLM (ISO 29148 atomization) ----
        formalize_provider, formalize_model = _resolve_role(
            settings.FORMALIZE_LLM_PROVIDER,
            settings.FORMALIZE_LLM_MODEL or (
                settings.OLLAMA_FORMALIZE_MODEL if (settings.FORMALIZE_LLM_PROVIDER or settings.LLM_PROVIDER) == "ollama" else ""
            ),
        )
        self.formalize_llm = _build_llm(
            provider=formalize_provider,
            model=formalize_model,
            temperature=settings.OLLAMA_FORMALIZE_TEMPERATURE,
            max_tokens=settings.OLLAMA_FORMALIZE_NUM_PREDICT,
            json_mode=True,
        )

        logger.info(
            "LLM providers — main=%s/%s, analysis=%s/%s, formalize=%s/%s",
            main_provider, main_model or "<default>",
            analysis_provider, analysis_model or "<default>",
            formalize_provider, formalize_model or "<default>",
        )
        
        # Initialize state persister
        self.checkpointer = MemorySaver()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("RequirementsAnalysisAgent initialized")
    
    def _build_workflow(self):
        """Build LangGraph workflow for requirements analysis.

        Pipeline (2 LLM calls instead of the original 4):
          analyze_quality  — smell detection + gap scoring in one fast call
          formalize        — ISO 29148 formatting with the full-capability model
          consolidate      — decide whether to interrupt
          generate_questions | export_ready
        """
        workflow = StateGraph(AgentState)

        workflow.add_node("analyze_quality", self._analyze_quality_node)
        workflow.add_node("formalize", self._formalize_node)
        workflow.add_node("consolidate", self._consolidate_results_node)
        workflow.add_node("generate_questions", self._generate_questions_node)
        workflow.add_node("export_ready", self._export_ready_node)

        workflow.add_edge("analyze_quality", "formalize")
        workflow.add_edge("formalize", "consolidate")

        workflow.add_conditional_edges(
            "consolidate",
            self._should_interrupt,
            {True: "generate_questions", False: "export_ready"},
        )

        workflow.add_edge("generate_questions", END)
        workflow.add_edge("export_ready", END)

        workflow.set_entry_point("analyze_quality")

        return workflow
    
    async def analyze(self, state: RequirementAnalysisState) -> Dict[str, Any]:
        """
        Run the analysis workflow (non-blocking — wraps sync LangGraph invoke in a thread).

        Args:
            state: Initial analysis state

        Returns:
            Final analysis response
        """
        logger.info(f"Starting analysis for session {state.session_id}")

        try:
            # Convert Pydantic model to dict for LangGraph.
            # Explicitly reset clarification fields so a fresh analysis on the same
            # session_id doesn't inherit answered questions from a previous checkpoint
            # and incorrectly suppress the interrupt via _should_interrupt.
            state_dict: AgentState = {
                "session_id": state.session_id,
                "input_text": state.input_text,
                "context_docs": [doc.model_dump() if hasattr(doc, 'model_dump') else doc for doc in (state.context_docs or [])],
                "status": state.status.value if hasattr(state.status, 'value') else str(state.status),
                "interrupt_needed": False,
                "user_clarifications": {},
                "clarification_questions": [],
            }

            # Run the workflow in a thread so the async event loop stays unblocked
            result = await asyncio.to_thread(
                self.app.invoke,
                state_dict,
                {"configurable": {"thread_id": state.session_id}},
            )

            logger.info(f"Analysis complete for session {state.session_id}")

            # Ensure result is a dict and convert Pydantic objects to dicts
            if isinstance(result, dict):
                result_dict = result
            else:
                result_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)

            # Convert Pydantic objects to dicts for JSON serialization
            if "smells" in result_dict and result_dict["smells"]:
                result_dict["smells"] = [
                    s.model_dump() if hasattr(s, 'model_dump') else s
                    for s in result_dict["smells"]
                ]

            if "clarification_questions" in result_dict and result_dict["clarification_questions"]:
                result_dict["clarification_questions"] = [
                    q.model_dump() if hasattr(q, 'model_dump') else q
                    for q in result_dict["clarification_questions"]
                ]

            if "requirements" in result_dict and result_dict["requirements"]:
                result_dict["requirements"] = [
                    r.model_dump() if hasattr(r, 'model_dump') else r
                    for r in result_dict["requirements"]
                ]

            logger.info(f"Result state keys: {list(result_dict.keys())}")
            logger.info(f"Requirements count: {len(result_dict.get('requirements', []))}")
            logger.info(f"Status: {result_dict.get('status')}")

            return result_dict

        except Exception as e:
            logger.error(f"Analysis error: {str(e)}", exc_info=True)
            raise
    
    async def resume_after_clarification(
        self, session_id: str, clarifications: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Resume workflow after user provides clarifications.

        Reads existing state, merges clarifications into user_clarifications, and
        re-runs the full pipeline so the formalizer picks them up.

        Args:
            session_id: Session ID
            clarifications: User's clarification answers {question_id: answer}

        Returns:
            Updated analysis response
        """
        logger.info(f"Resuming analysis with clarifications for session {session_id}")

        try:
            config = {"configurable": {"thread_id": session_id}}

            # Read previous state to get the original input text and any prior clarifications
            existing = self.app.get_state(config)
            if not existing.values:
                raise ValueError(f"No existing state for session {session_id}")

            existing_clarifications = existing.values.get("user_clarifications") or {}
            merged_clarifications = {**existing_clarifications, **clarifications}

            # Carry over the clarification_questions from the interrupted run so the
            # formalizer can pair each question_id with its user answer. Without this,
            # if the resumed pipeline re-enters _generate_questions_node and regenerates
            # questions with fresh IDs, the user's answers (keyed by the OLD IDs) would
            # be silently dropped.
            prior_questions = existing.values.get("clarification_questions") or []

            state_dict: AgentState = {
                "session_id": session_id,
                "input_text": existing.values.get("input_text", ""),
                "context_docs": existing.values.get("context_docs", []),
                "status": "clarified",
                "interrupt_needed": False,
                "user_clarifications": merged_clarifications,
                "clarification_questions": prior_questions,
                # Carry over the round counter so the iterative clarification
                # loop (Bug 3) can decide whether to ask another batch.
                "clarification_round": existing.values.get("clarification_round", 0),
            }

            # Re-run pipeline in a thread (now formalizer will see user_clarifications)
            result = await asyncio.to_thread(
                self.app.invoke,
                state_dict,
                {"configurable": {"thread_id": session_id}},
            )

            if isinstance(result, dict):
                result_dict = result
            else:
                result_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)

            if "smells" in result_dict and result_dict["smells"]:
                result_dict["smells"] = [
                    s.model_dump() if hasattr(s, 'model_dump') else s
                    for s in result_dict["smells"]
                ]

            if "clarification_questions" in result_dict and result_dict["clarification_questions"]:
                result_dict["clarification_questions"] = [
                    q.model_dump() if hasattr(q, 'model_dump') else q
                    for q in result_dict["clarification_questions"]
                ]

            if "requirements" in result_dict and result_dict["requirements"]:
                result_dict["requirements"] = [
                    r.model_dump() if hasattr(r, 'model_dump') else r
                    for r in result_dict["requirements"]
                ]

            logger.info(f"Analysis resumed for session {session_id}")
            logger.info(f"Requirements count: {len(result_dict.get('requirements', []))}")
            logger.info(f"Status: {result_dict.get('status')}")

            return result_dict

        except Exception as e:
            logger.error(f"Resume error: {str(e)}")
            raise
    
    # ---- Workflow Nodes ----

    def _should_regenerate_questions(self, state: Dict[str, Any]) -> bool:
        """
        Decide whether to regenerate fresh clarification questions on a resume run.

        Returns True when ALL prior questions have been answered AND overall
        quality is still below the target — meaning we need a *new*, deeper
        round of questions (Bug 3 — iterative clarification). Returns False
        when prior questions are not yet fully answered (preserve & resume) or
        when overall quality already meets target.
        """
        existing_questions = state.get("clarification_questions") or []
        user_clarifications = state.get("user_clarifications") or {}
        if not existing_questions or not user_clarifications:
            return False

        prior_ids = {
            q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None)
            for q in existing_questions
        }
        answered_ids = {qid for qid, ans in user_clarifications.items() if ans}
        all_answered = bool(prior_ids) and prior_ids.issubset(answered_ids)
        if not all_answered:
            return False

        # All prior answered: regenerate only if quality still below target and
        # we have rounds left.
        formalized = state.get("formalized")
        overall = (
            formalized.get("overall_score", 0.0)
            if isinstance(formalized, dict)
            else 0.0
        )
        current_round = state.get("clarification_round", 0)
        return (
            overall < settings.QUALITY_TARGET_SCORE
            and current_round < settings.MAX_CLARIFICATION_ROUNDS
        )

    def _ensure_dict(self, state: Any) -> Dict[str, Any]:
        """Convert state to dict if it's a Pydantic model."""
        if isinstance(state, dict):
            return state
        return state.model_dump()
    
    def _parse_input_node(self, state: AgentState) -> AgentState:
        """Parse and normalize input text."""
        logger.info("Executing: Parse Input Node")
        
        input_text = state.get("input_text", "")
        
        # Use LLM to extract structured info
        parse_prompt = f"""
Analyze this requirement input and extract:
1. Main subject/stakeholder
2. Desired action/capability
3. Business goal
4. Constraints mentioned

Input: {input_text}

Respond with structured analysis.
"""
        
        analysis = self.llm.invoke(parse_prompt)
        logger.info(f"Input parsed: {analysis[:100]}")
        
        state["parsed_analysis"] = analysis
        state["status"] = "analyzing"
        
        return state
    
    def _analyze_quality_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Combined smell detection + logical gap scoring in a single LLM call.

        Replaces the old parse_input → detect_smells → analyze_logic chain (3 calls)
        with one call to analysis_llm (optionally a smaller/faster model).
        Sets: smells, smell_score, logical_gap_score, status, parsed_analysis.
        """
        import json as _json

        logger.info("Executing: Quality Analysis Node (smell + gap)")

        state = self._ensure_dict(state)
        input_text = state.get("input_text", "")

        if "requirements" not in state:
            state["requirements"] = []

        quality_prompt = f"""You are a requirements quality analyst. Analyze this requirement text.

Text:
{input_text}

Return ONLY this JSON (no markdown, no explanation):
{{
  "smells": [
    {{
      "type": "ambiguous",
      "severity": 0.85,
      "location": "exact quoted phrase from the text",
      "recommendation": "specific actionable fix"
    }}
  ],
  "gap_score": 0.75
}}

Smell types:
- ambiguous: vague words (fast, secure, easy, flexible, better, modern, good, clean, intuitive)
- incomplete: missing who/what/when/how much
- unmeasurable: no concrete metric or threshold
- infeasible: cannot be implemented or verified as stated
- conflicting: contradicts another statement in the same text
- scope_creep: multiple unrelated concerns bundled together

severity: 0.0 = minor, 1.0 = critical
gap_score: 0.0 = fully specified and implementable, 1.0 = completely vague
smells: use [] if the text is clear, specific, and well-specified"""

        try:
            response = self.analysis_llm.invoke(quality_prompt)
        except Exception as e:
            logger.warning(f"Quality analysis LLM invoke failed ({type(e).__name__}: {e}); using fallback scores")
            response = '{"smells":[{"type":"ambiguous","severity":0.8,"location":"","recommendation":"Requirement needs clarification"}],"gap_score":0.7}'
        logger.info(f"Quality analysis raw response: {str(response)[:200]}")

        smells: List[RequirementSmellAnalysis] = []
        gap_score = 0.5

        try:
            raw = response.content if hasattr(response, "content") else response
            parsed = _json.loads(raw) if isinstance(raw, str) else raw
            raw_smells = parsed.get("smells", [])
            gap_score = float(parsed.get("gap_score", 0.5))

            for s in raw_smells:
                smells.append(RequirementSmellAnalysis(
                    smell_type=self._map_smell_type(s.get("type", "ambiguous")),
                    severity=float(s.get("severity", 0.5)),
                    location=s.get("location", input_text[:80]),
                    recommendation=s.get("recommendation", "Clarify this requirement"),
                ))
        except Exception as e:
            logger.warning(f"Quality analysis parse error: {e} — applying fallback smell")
            smells.append(RequirementSmellAnalysis(
                smell_type=RequirementSmell.AMBIGUOUS,
                severity=0.8,
                location=input_text[:80],
                recommendation="Requirement needs clarification with specific, measurable criteria",
            ))
            gap_score = 0.7

        smell_score = min(1.0, sum(s.severity for s in smells))

        logger.info(
            f"Quality analysis complete. smell_score={smell_score:.2f} "
            f"({len(smells)} smells), gap_score={gap_score:.2f}"
        )

        state["smells"] = [s.model_dump() for s in smells]
        state["smell_score"] = smell_score
        state["logical_gap_score"] = gap_score
        state["parsed_analysis"] = f"smell_score={smell_score:.2f}, gap_score={gap_score:.2f}"
        state["status"] = "analyzing"

        return state

    def _detect_smells_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect requirement smells.
        
        Returns smells and calculates smell score to determine if interruption needed.
        Preserves existing requirements (SCRIBE MODE).
        """
        logger.info("Executing: Smell Detection Node")
        
        state = self._ensure_dict(state)
        input_text = state.get("input_text", "")
        
        # Preserve existing requirements (SCRIBE MODE)
        if "requirements" not in state:
            state["requirements"] = []
        
        smell_prompt = f"""You are a requirements quality analyst. Detect requirement smells in the text below.

Smell types to check:
- ambiguous: vague words like "fast", "secure", "easy", "flexible", "better", "good", "modern"
- incomplete: missing who/what/when/how much
- unmeasurable: no concrete metric or acceptance threshold
- infeasible: impossible to verify or implement
- conflicting: contradicts another statement
- scope_creep: multiple unrelated concerns in one requirement

Input text:
{input_text}

RULES:
- Return ONLY a raw JSON array. No markdown. No explanation. No code fences.
- Each item: {{"type": "ambiguous", "severity": 0.85, "location": "exact quoted phrase", "recommendation": "specific fix"}}
- severity: 0.0-1.0 where 1.0 is worst
- If no smells found, return: []

JSON array:"""

        smells_response = self.llm.invoke(smell_prompt)
        if hasattr(smells_response, "content"):
            smells_response = smells_response.content

        if not smells_response:
            logger.error("Ollama returned empty response for smells")

        # Parse LLM response to extract smells
        smells = self._parse_smell_response(smells_response, input_text)

        # Accumulative score: each smell adds its severity so more problems = higher score.
        # Capped at 1.0. This replaces the old average which diluted multiple smells.
        smell_score = min(1.0, sum(s.severity for s in smells))
        
        logger.info(f"Smell detection complete. Score: {smell_score:.2f}, Smells found: {len(smells)}")
        
        state["smells"] = smells
        state["smell_score"] = smell_score
        
        return state
    
    def _should_interrupt(self, state: AgentState) -> bool:
        """
        Determine if workflow should interrupt for human clarification.

        Triggers when smell score OR logical gap score exceeds its threshold.

        Iteration policy (Bug 3 fix):
        - On the first pass we always interrupt when quality is poor.
        - On a resume pass (user has answered prior questions), we re-evaluate:
            * If we have already hit MAX_CLARIFICATION_ROUNDS → stop, force export.
            * If overall_score >= QUALITY_TARGET_SCORE → quality target reached,
              stop interrupting.
            * Otherwise → quality is still poor; allow another interrupt round
              with fresh, more-targeted questions.
        """
        smell_score = state.get("smell_score", 0.0)
        logical_gap_score = state.get("logical_gap_score", 0.0)

        smell_trigger = smell_score >= settings.SMELL_SCORE_THRESHOLD
        gap_trigger = logical_gap_score >= settings.LOGICAL_GAP_THRESHOLD
        should_interrupt = smell_trigger or gap_trigger

        user_clarifications = state.get("user_clarifications") or {}
        prior_questions = state.get("clarification_questions") or []
        if should_interrupt and user_clarifications and prior_questions:
            current_round = state.get("clarification_round", 0)
            if current_round >= settings.MAX_CLARIFICATION_ROUNDS:
                logger.info(
                    f"Max clarification rounds ({settings.MAX_CLARIFICATION_ROUNDS}) "
                    f"reached — forcing export despite low quality."
                )
                should_interrupt = False
            else:
                formalized = state.get("formalized")
                overall = (
                    formalized.get("overall_score", 0.0)
                    if isinstance(formalized, dict)
                    else 0.0
                )
                if overall >= settings.QUALITY_TARGET_SCORE:
                    logger.info(
                        f"Quality target reached ({overall:.2f} >= "
                        f"{settings.QUALITY_TARGET_SCORE}) — no further interrupt."
                    )
                    should_interrupt = False
                else:
                    # Still poor quality. Only re-interrupt once the user has
                    # actually finished answering the prior batch — otherwise
                    # mid-flight resume calls would prematurely re-ask.
                    prior_ids = {
                        q.get("question_id") if isinstance(q, dict)
                        else getattr(q, "question_id", None)
                        for q in prior_questions
                    }
                    answered_ids = {
                        qid for qid, ans in user_clarifications.items() if ans
                    }
                    if prior_ids and prior_ids.issubset(answered_ids):
                        logger.info(
                            f"Quality still low ({overall:.2f}) after round "
                            f"{current_round} — allowing re-interrupt with fresh "
                            f"questions."
                        )
                        # Leave should_interrupt True so a fresh question batch fires.
                    else:
                        # User hasn't finished answering — suppress to avoid
                        # double-prompting mid-flight.
                        logger.info(
                            "Suppressing interrupt: prior clarification questions "
                            "not yet fully answered."
                        )
                        should_interrupt = False

        logger.info(
            f"Interrupt check: smell={smell_score:.2f}(>={settings.SMELL_SCORE_THRESHOLD}={smell_trigger}), "
            f"gap={logical_gap_score:.2f}(>={settings.LOGICAL_GAP_THRESHOLD}={gap_trigger}), "
            f"round={state.get('clarification_round', 0)}, interrupt={should_interrupt}"
        )
        return should_interrupt
    
    def _analyze_logic_node(self, state: AgentState) -> AgentState:
        """
        Analyze logical consistency and gaps.
        Preserves existing requirements (SCRIBE MODE).
        """
        logger.info("Executing: Logic Analysis Node")
        
        input_text = state.get("input_text", "")
        smells = state.get("smells", [])
        
        # Preserve existing requirements (SCRIBE MODE)
        if "requirements" not in state:
            state["requirements"] = []
        
        logic_prompt = f"""You are a requirements analyst. Assess the logical completeness of this requirement text.

Text:
{input_text}

Check for:
1. Missing actor or system subject
2. Missing measurable success criteria
3. Undefined terms or jargon
4. Dependencies on unstated assumptions
5. Contradictions between statements

Rate the gap_score from 0.0 to 1.0 where:
- 1.0 = extremely vague, missing most details, cannot be implemented as-is
- 0.5 = partially specified, some gaps
- 0.0 = fully specified, no gaps

Respond with exactly this line and nothing else:
gap_score: X.XX"""

        logic_analysis = self.llm.invoke(logic_prompt)
        logical_gap_score = self._extract_score(logic_analysis)
        
        logger.info(f"Logic analysis complete. Gap score: {logical_gap_score:.2f}")
        
        state["logical_gap_score"] = logical_gap_score
        state["logic_analysis"] = logic_analysis
        
        return state
    
    def _generate_questions_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clarification questions for interruption.

        If user_clarifications already exist for all previously-generated questions
        (i.e. we are on a resume run after the user answered), preserve the existing
        questions so _formalize_node's question_id → answer lookup keeps working.
        Otherwise, generate fresh questions from the LLM. Also sets status to
        'needs_clarification' so downstream consumers can distinguish an interrupted
        session from a completed formal draft.
        """
        logger.info("Executing: Question Generation Node")

        state = self._ensure_dict(state)
        input_text = state.get("input_text", "")
        smells = state.get("smells", [])
        existing_questions = state.get("clarification_questions") or []
        user_clarifications = state.get("user_clarifications") or {}

        # If we already have questions AND the user has answered at least one of them,
        # keep the existing questions so the formalizer can still match IDs → answers.
        # Regenerating would produce new question_ids that don't match user_clarifications,
        # silently dropping the user's answers on resume.
        answered_ids = {qid for qid, ans in user_clarifications.items() if ans}
        existing_ids = {
            q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None)
            for q in existing_questions
        }
        if existing_questions and answered_ids & existing_ids and not self._should_regenerate_questions(state):
            logger.info(
                f"Preserving {len(existing_questions)} existing clarification questions "
                f"(user has answered {len(answered_ids & existing_ids)} of them)"
            )
            questions = existing_questions
        else:
            # Format smells as readable bullet points (severity + type + location +
            # recommendation). Pass ALL smells so severe ones at index 3+ are not
            # silently dropped (Bug 1 fix).
            def _smell_bullet(s: Any) -> str:
                if isinstance(s, dict):
                    stype = s.get("smell_type") or s.get("type") or "quality_issue"
                    loc = s.get("location") or "(unspecified)"
                    sev = s.get("severity", 0.0)
                    rec = s.get("recommendation") or s.get("description") or ""
                else:
                    stype = getattr(s, "smell_type", None) or getattr(s, "type", None) or "quality_issue"
                    loc = getattr(s, "location", None) or "(unspecified)"
                    sev = getattr(s, "severity", 0.0)
                    rec = getattr(s, "recommendation", None) or getattr(s, "description", "") or ""
                # Normalize enum objects and "ClassName.VALUE" strings to plain value
                if hasattr(stype, "value"):
                    stype = stype.value
                elif isinstance(stype, str) and "." in stype:
                    stype = stype.split(".")[-1].lower()
                try:
                    sev_f = float(sev)
                except (TypeError, ValueError):
                    sev_f = 0.0
                return f"- [severity={sev_f:.2f}] requirement not clear at \"{loc}\" — {rec}".strip()

            smell_bullets = "\n".join(_smell_bullet(s) for s in (smells or []))
            if not smell_bullets:
                smell_bullets = "(no specific smells detected — focus on completeness, measurability, and unambiguous wording)"

            # On round 2+ include a summary of what was already asked/answered
            # so the LLM avoids repeating itself and digs deeper.
            current_round = state.get("clarification_round", 0)
            prior_qa_block = ""
            if current_round >= 1 and existing_questions:
                lines = []
                for q in existing_questions:
                    qid = q.get("question_id") if isinstance(q, dict) else getattr(q, "question_id", None)
                    qtext = q.get("question") if isinstance(q, dict) else getattr(q, "question", "")
                    ans = user_clarifications.get(qid, "(no answer)") if qid else "(no answer)"
                    lines.append(f"- Q: {qtext}\n  A: {ans}")
                prior_qa_block = (
                    "\n\nPrevious clarification round (DO NOT repeat these questions; ask DIFFERENT, "
                    "deeper questions that build on the answers below):\n" + "\n".join(lines)
                )

            questions_prompt = f"""You are a senior requirements engineer (ISO/IEC/IEEE 29148). Your job is to ask clarification questions that turn a vague requirement into a TESTABLE one.

A good clarification question:
- Targets ONE specific quality defect from the issues list below.
- Asks WHO (actor/role), WHAT (precise behaviour or output), WHEN (trigger/condition), or HOW MUCH (numeric threshold, units, tolerance).
- Is concrete and answerable — e.g. "What is the maximum acceptable response time in milliseconds under peak load?" NOT "Can you clarify performance?"
- Forces the user to commit to a measurable acceptance criterion.

Original input requirement text:
\"\"\"
{input_text}
\"\"\"

Identified quality issues (each one is a defect to address with at least one question, ordered by severity high→low):
{smell_bullets}{prior_qa_block}

Produce 3-5 questions, ordered by severity (most critical first). Each question MUST clearly map to one of the issues above. Avoid generic questions; if you cannot tie a question to a specific issue, omit it.

Respond with ONLY valid JSON in exactly this schema (no prose, no markdown fences):
[
  {{"question_id": "q1", "question": "<the concrete question>", "context": "<which smell/defect this targets and why it matters>", "required_clarity": ["<measurable attribute 1>", "<measurable attribute 2>"]}}
]
"""

            try:
                questions_response = self.llm.invoke(questions_prompt)
            except Exception as e:
                logger.warning(f"Question generation LLM invoke failed ({type(e).__name__}: {e}); using empty fallback")
                questions_response = "[]"
            if hasattr(questions_response, "content"):
                questions_response = questions_response.content
            questions = self._parse_questions_response(questions_response)

            # Bump the round counter only when we actually emit a fresh batch of
            # questions (Bug 3). Preserving the prior batch is not a new round.
            state["clarification_round"] = state.get("clarification_round", 0) + 1
            logger.info(
                f"Clarification round bumped to {state['clarification_round']} "
                f"(max={settings.MAX_CLARIFICATION_ROUNDS})"
            )

            # Fallback: if the LLM produced no parseable questions but we still need an
            # interrupt, emit a generic question so the interrupt is actionable and the
            # frontend doesn't hang waiting for questions that never arrive.
            if not questions:
                logger.warning(
                    "Question generation returned empty list; emitting fallback question "
                    "so the interrupt carries an actionable payload."
                )
                questions = [
                    ClarificationQuestion(
                        question_id="q_fallback_1",
                        question=(
                            "The requirement contains quality issues (ambiguity, "
                            "missing details, or unclear scope). Please provide "
                            "additional context or specifics to help formalize it."
                        ),
                        context="Auto-generated fallback — LLM did not return structured questions.",
                        required_clarity=["scope", "measurable criteria", "rationale"],
                    )
                ]

        logger.info(f"Generated {len(questions)} clarification questions")

        state["clarification_questions"] = [
            q.model_dump() if hasattr(q, "model_dump") else q for q in questions
        ]
        # Signal to downstream consumers (frontend, /formalize endpoint, WS handler)
        # that this session is interrupted awaiting clarification — NOT a completed draft.
        state["status"] = "needs_clarification"

        return state
    
    def _formalize_node(self, state: AgentState) -> AgentState:
        """
        Formalize requirements to ISO 29148 with proper shall statements.
        Uses LLM to create formally compliant requirements.
        """
        logger.info("Executing: Formalization Node")
        
        input_text = state.get("input_text", "")
        context_docs = state.get("context_docs", [])
        smells = state.get("smells", [])
        clarification_questions = state.get("clarification_questions", [])
        
        # Build context
        context_text = ""
        if context_docs:
            context_text = " ".join([str(doc.get("extracted_text", "")[:500]) for doc in context_docs])
        
        # Build clarifications — questions may be dicts or Pydantic objects (from checkpoint)
        def _qfield(q, field, default=""):
            return q.get(field, default) if isinstance(q, dict) else getattr(q, field, default)

        clarifications_text = ""
        if clarification_questions:
            user_clarifs = state.get("user_clarifications") or {}
            clarifications_text = "\n".join([
                f"Q: {_qfield(q, 'question')}\nA: {user_clarifs.get(_qfield(q, 'question_id', ''), '')}"
                for q in clarification_questions
            ])

        # Pre-count distinct features so we can give the LLM an explicit target.
        # Weak local models ignore generic "split if needed" instructions but reliably
        # comply when told the exact expected array length.
        feature_bullets, feature_count = self._extract_feature_list(input_text)
        feature_hint = (
            f"\nIDENTIFIED FEATURES ({feature_count} distinct):\n{feature_bullets}\n"
            f"Your output JSON array MUST contain exactly {feature_count} requirement object(s) — one per feature above.\n"
        )

        # Enhanced ISO 29148 formatting prompt
        context_header = "CONTEXT DOCUMENTS:\n" if context_text else ""
        clarifications_header = "CLARIFICATIONS PROVIDED:\n" if clarifications_text else ""
        formalize_prompt = f"""
System Role:
You are a Senior Requirements Engineer specialized in ISO 29148 standards. Your task is to perform "Requirement Atomization." You will take raw, messy stakeholder input and break it into discrete, formalized requirements.

The Rules of Atomization:
One Goal per Requirement: If a sentence contains "and" or multiple verbs, split it into two or more separate requirements.
Remove Subjectivity: Replace "fast," "easy," "user-friendly," and "scalable" with placeholders for measurable constraints (e.g., [Performance Constraint]).
The "Shall" Template: Every requirement must follow this structure:
[Entity] shall [Action] [Object] [Condition/Constraint]
Comma Separation: Treat commas as potential logical breaks for new requirements if they introduce a new action or object.

You are an ISO 29148 requirements specialist. Convert the following requirement into formally compliant ISO 29148 format.

ORIGINAL REQUIREMENT:
{input_text}

{feature_hint}
{context_header}{context_text if context_text else ''}

{clarifications_header}{clarifications_text if clarifications_text else ''}

TASK: The input above contains {feature_count} distinct feature(s) listed above. Split them into {feature_count} separate ISO 29148 compliant requirements. Each distinct user need or feature MUST become its own requirement in the output array.

ISO 29148 REQUIREMENTS:
1. Each requirement MUST use imperative "shall" language
2. Requirements must be testable/verifiable
3. Include clear title, shall statement, rationale, and acceptance criteria
4. Prioritize based on business impact
5. Categorize as Functional/Non-functional/Interface

OUTPUT FORMAT (JSON array with exactly {feature_count} items):
[
    {{
        "title": "Clear, concise title (< 80 chars)",
        "shall_statement": "The system shall [verb] [object] [constraint].",
        "rationale": "Business justification explaining why this requirement exists",
        "acceptance_criteria": [
            "Specific, measurable acceptance criterion 1",
            "Specific, measurable acceptance criterion 2",
            "Specific, measurable acceptance criterion 3"
        ],
        "priority": "High|Medium|Low",
        "category": "Functional|Non-functional|Interface",
        "depends_on": []
    }}
]

OUTPUT ONLY VALID JSON, NO MARKDOWN OR EXPLANATIONS.
"""
        
        try:
            formalize_response = self.formalize_llm.invoke(formalize_prompt)
            if hasattr(formalize_response, "content"):
                formalize_response = formalize_response.content
            logger.info(f"LLM formalization response: {formalize_response}")

            # Parse JSON response
            iso_requirements = self._parse_formalize_response(formalize_response)
            
            # Ensure we have a list
            if not isinstance(iso_requirements, list):
                logger.error(f"Expected list from _parse_formalize_response, got {type(iso_requirements)}")
                iso_requirements = []
            
            # Enhance with IDs - only for dict items
            valid_requirements = []
            for i, req in enumerate(iso_requirements, 1):
                if isinstance(req, dict):
                    req["requirement_id"] = f"REQ-{i:04d}"
                    valid_requirements.append(req)
                else:
                    logger.warning(f"Skipping non-dict requirement: {type(req)} - {str(req)[:100]}")
            
            logger.info(f"Formalization complete: {len(valid_requirements)} requirements created")

            # Determine interrupt before setting formalized so ready_for_export is consistent
            smell_score = state.get("smell_score", 0.0)
            interrupt_needed = smell_score >= settings.SMELL_SCORE_THRESHOLD
            state["requirements"] = valid_requirements
            state["status"] = "formal_draft"
            state["interrupt_needed"] = interrupt_needed
            completeness_score = self._calculate_requirements_completeness(valid_requirements)
            # Attach per-requirement smell-based quality score (and compute the
            # document-level average). Smells are already populated by the
            # prior analyze_quality node. This is pure text-matching — no
            # extra LLM calls — so it is safe to run inline here.
            quality_score = self._attach_per_requirement_quality(
                valid_requirements, state.get("smells", []) or []
            )

            # Combined per-requirement score (Bug 2 fix): the frontend should
            # display ONE score per card that reflects both completeness (ISO
            # field coverage) and quality (smell-derived defects). Showing
            # quality_score alone produced the misleading "100% per card vs 20%
            # total" contradiction.
            overall_total = 0.0
            for req in valid_requirements:
                comp = float(req.get("completeness_score", 0.0) or 0.0)
                qual = float(req.get("quality_score", 0.0) or 0.0)
                req["overall_score"] = round((comp + qual) / 2.0, 4)
                overall_total += req["overall_score"]
            overall_score = (
                round(overall_total / len(valid_requirements), 4)
                if valid_requirements
                else 0.0
            )

            state["formalized"] = {
                "total_requirements": len(valid_requirements),
                "completeness_score": completeness_score,
                "quality_score": quality_score,
                "overall_score": overall_score,
                # Only export-ready when there are requirements AND no pending interrupt
                "ready_for_export": bool(valid_requirements) and not interrupt_needed,
            }
            logger.info(f"Interrupt flag set to {interrupt_needed} based on smell_score {smell_score:.2f}")
            
        except Exception as e:
            logger.error(f"Formalization error: {str(e)}")
            state["status"] = "formalization_failed"
            state["requirements"] = []
            state["interrupt_needed"] = True  # Interrupt on error so user knows
        
        return state
    
    def _export_ready_node(self, state: AgentState) -> AgentState:
        """Final check and mark as export-ready."""
        logger.info("Executing: Export Ready Node")
        
        state["status"] = "export_ready"
        
        return state
    
    def _consolidate_results_node(self, state: AgentState) -> AgentState:
        """
        Consolidate results and sync interrupt_needed with the routing logic.

        Must run BEFORE _should_interrupt so the final state reflects the actual
        decision that will be taken — otherwise the API response and the routing
        disagree (e.g. gap triggers questions but state still says interrupt=False).
        """
        logger.info("Executing: Consolidate Results Node")

        # Ensure all critical fields are present
        if "smell_score" not in state:
            state["smell_score"] = 0.0
        if "logical_gap_score" not in state:
            state["logical_gap_score"] = 0.0
        if "requirements" not in state:
            state["requirements"] = []
        if "smells" not in state:
            state["smells"] = []

        # Keep interrupt_needed in sync with _should_interrupt's logic so callers
        # reading state (API endpoints, WebSocket) see the correct value — including
        # the "all prior questions already answered" loop-breaker below.
        interrupt_needed = self._should_interrupt(state)
        state["interrupt_needed"] = interrupt_needed
        smell_score = state.get("smell_score", 0.0)
        logical_gap_score = state.get("logical_gap_score", 0.0)

        # Also keep ready_for_export consistent with updated interrupt flag
        if "formalized" in state and isinstance(state["formalized"], dict):
            state["formalized"]["ready_for_export"] = (
                bool(state.get("requirements")) and not interrupt_needed
            )

        logger.info(
            f"Consolidated: smell={smell_score:.2f}, gap={logical_gap_score:.2f}, "
            f"interrupt={interrupt_needed}, reqs={len(state.get('requirements', []))}"
        )
        return state
    
    # ---- Helper Methods ----
    
    # Maps keywords the LLM may produce to our enum values
    _SMELL_KEYWORD_MAP = {
        "ambiguous": RequirementSmell.AMBIGUOUS,
        "vague": RequirementSmell.AMBIGUOUS,
        "imprecise": RequirementSmell.AMBIGUOUS,
        "incomplete": RequirementSmell.INCOMPLETE,
        "missing": RequirementSmell.INCOMPLETE,
        "infeasible": RequirementSmell.INFEASIBLE,
        "impossible": RequirementSmell.INFEASIBLE,
        "conflicting": RequirementSmell.CONFLICTING,
        "contradiction": RequirementSmell.CONFLICTING,
        "unmeasurable": RequirementSmell.UNMEASURABLE,
        "no metric": RequirementSmell.UNMEASURABLE,
        "scope": RequirementSmell.VAGUE_SCOPE,
        "rationale": RequirementSmell.MISSING_RATIONALE,
        "justification": RequirementSmell.MISSING_RATIONALE,
    }

    def _map_smell_type(self, raw: str) -> RequirementSmell:
        """Map a verbose LLM string to a RequirementSmell enum value."""
        lower = raw.lower()
        for keyword, enum_val in self._SMELL_KEYWORD_MAP.items():
            if keyword in lower:
                return enum_val
        # Try exact enum match as fallback
        try:
            return RequirementSmell(raw.lower())
        except ValueError:
            return RequirementSmell.AMBIGUOUS

    def _parse_smell_response(
        self, llm_response: str, original_text: str
    ) -> List[RequirementSmellAnalysis]:
        """Parse LLM response into RequirementSmellAnalysis objects."""
        import json
        import re

        smells = []
        try:
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                smells_data = json.loads(json_match.group())
                for smell_data in smells_data:
                    raw_type = smell_data.get("type", "ambiguous")
                    smell = RequirementSmellAnalysis(
                        smell_type=self._map_smell_type(raw_type),
                        severity=float(smell_data.get("severity", 0.5)),
                        location=smell_data.get("location", original_text[:50]),
                        recommendation=smell_data.get("recommendation", "Clarify requirement"),
                    )
                    smells.append(smell)
            else:
                # LLM returned prose instead of JSON — treat the whole response as
                # evidence that smells exist (it wouldn't write paragraphs for clean input).
                logger.warning("Smell response contained no JSON array — adding prose fallback smell")
                smells.append(RequirementSmellAnalysis(
                    smell_type=RequirementSmell.AMBIGUOUS,
                    severity=0.8,
                    location=original_text[:80],
                    recommendation="Requirement needs clarification — specify measurable criteria",
                ))

        except Exception as e:
            logger.warning(f"Error parsing smell response: {str(e)}")
            smells.append(RequirementSmellAnalysis(
                smell_type=RequirementSmell.AMBIGUOUS,
                severity=0.8,
                location=original_text[:50],
                recommendation="Please clarify the requirement with specific, measurable criteria",
            ))

        return smells
    
    def _parse_questions_response(self, llm_response: str) -> List[ClarificationQuestion]:
        """Parse LLM response into ClarificationQuestion objects."""
        questions = []
        
        try:
            import json
            import re
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                questions_data = json.loads(json_match.group())
                for q_data in questions_data:
                    question = ClarificationQuestion(
                        question_id=q_data.get("question_id", f"q{len(questions) + 1}"),
                        question=q_data.get("question", "Please clarify"),
                        context=q_data.get("context"),
                        required_clarity=q_data.get("required_clarity", []),
                    )
                    questions.append(question)
        
        except Exception as e:
            logger.warning(f"Error parsing questions response: {str(e)}")
        
        return questions
    
    def _extract_score(self, text: str) -> float:
        """Extract a 0-1 score from LLM response, preferring labeled values."""
        import re
        try:
            # Prefer labeled patterns: "score: 0.7", "consistency: 0.85", "gap: 0.3"
            labeled = re.search(
                r'(?:score|gap|consistency|rating|quality)[\s:=]+([01](?:\.\d+)?)',
                text,
                re.IGNORECASE,
            )
            if labeled:
                return float(labeled.group(1))

            # Fall back: find a standalone decimal like "0.72" or "0.8" that is clearly 0-1
            decimal = re.search(r'\b0\.\d+\b', text)
            if decimal:
                return float(decimal.group())

            return 0.5
        except Exception:
            return 0.5
    
    def _parse_formalize_response(
        self, llm_response: str
    ) -> List[Dict[str, Any]]:
        """Parse LLM formalization response into requirement dicts."""
        requirements = []
        
        try:
            import json
            import re
            
            # Clean up response - remove markdown code blocks
            cleaned_response = llm_response.strip()
            # Remove ```json or ``` markers
            cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
            cleaned_response = re.sub(r'```\s*', '', cleaned_response)
            
            # Try to parse as valid JSON array first
            try:
                parsed = json.loads(cleaned_response)
                if isinstance(parsed, list):
                    requirements = parsed
                    logger.info(f"Parsed {len(requirements)} requirements from direct JSON parse")
                elif isinstance(parsed, dict):
                    # Check if it's wrapped in a "requirements" key
                    if "requirements" in parsed:
                        requirements = parsed["requirements"]
                        logger.info(f"Parsed {len(requirements)} requirements from dict with requirements key")
                    else:
                        requirements = [parsed]
                        logger.info("Parsed 1 requirement from direct JSON parse")
            except json.JSONDecodeError:
                # Try extracting JSON array from response (handle markdown-wrapped arrays)
                # Match array that may be inside markdown code blocks
                json_match = re.search(r'\[[\s\S]*\]', cleaned_response)
                if json_match:
                    try:
                        requirements = json.loads(json_match.group())
                        logger.info(f"Parsed {len(requirements)} requirements from extracted JSON array")
                    except json.JSONDecodeError:
                        # Try to find each requirement object individually
                        req_matches = re.findall(r'\{[^{}]*"title"[^{}]*\}', cleaned_response)
                        for match in req_matches:
                            try:
                                requirements.append(json.loads(match))
                            except:
                                pass
                        logger.info(f"Parsed {len(requirements)} requirements from individual objects")
                else:
                    # Try to extract single JSON object
                    json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                    if json_match:
                        obj = json.loads(json_match.group())
                        if isinstance(obj, dict):
                            requirements = [obj]
                            logger.warning("Parsed single requirement object instead of array")
                        elif isinstance(obj, list):
                            requirements = obj
                    else:
                        logger.warning("Could not parse any JSON from formalization response")
                        requirements = []
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in formalize response: {str(e)}")
            requirements = []
        except Exception as e:
            logger.error(f"Error parsing formalize response: {str(e)}")
            requirements = []
        
        # Ensure all items are dicts
        valid_reqs = []
        for req in requirements:
            if isinstance(req, dict):
                valid_reqs.append(req)
            else:
                logger.warning(f"Skipping non-dict item in requirements: {type(req)}")
        
        return valid_reqs

    def _extract_feature_list(self, text: str) -> tuple[list[str], int]:
        """
        Split raw stakeholder text into a list of distinct feature phrases.

        Uses conjunction/separator heuristics so the formalize prompt can tell
        the LLM exactly how many JSON array items to produce — the single most
        effective technique for getting weak local models to generate multiple
        requirements instead of collapsing everything into one.

        Returns (bullet_lines_str, count) where bullet_lines_str is a
        newline-joined numbered list ready to embed in a prompt.
        """
        import re

        # Sentence-level separators that almost always signal a new feature:
        #   "and I also want", "plus", "I also need", "additionally", "as well as",
        #   "furthermore", "moreover", "also", sentence boundary before "I want/need".
        # We split on these, then re-join fragments that are too short (< 6 words)
        # with the previous fragment to avoid over-splitting "A and B" short phrases.
        SEP = re.compile(
            r"""
            (?:,?\s+and\s+(?:I\s+(?:also\s+)?(?:want|need|would\s+like)\s+(?:them?\s+to\s+be\s+able\s+to\s+)?))|  # "and I (also) want/need"
            (?:,\s*plus\b)|                    # ", plus"
            (?:\.\s+(?=[A-Z]))|                # sentence boundary
            (?:;\s*)|                           # semicolons
            (?:\s+additionally[,\s]+)|          # "additionally"
            (?:\s+furthermore[,\s]+)|           # "furthermore"
            (?:\s+moreover[,\s]+)|              # "moreover"
            (?:\s+as\s+well\s+as\s+)           # "as well as"
            """,
            re.VERBOSE | re.IGNORECASE,
        )

        fragments = [f.strip() for f in SEP.split(text) if f and f.strip()]

        # Merge very-short fragments (< 5 words) back onto the previous one —
        # they're usually continuations, not new requirements.
        merged: list[str] = []
        for frag in fragments:
            if merged and len(frag.split()) < 5:
                merged[-1] = merged[-1].rstrip(" .,") + ", " + frag
            else:
                merged.append(frag)

        # Always have at least 1 feature
        if not merged:
            merged = [text.strip()]

        bullets = "\n".join(f"{i+1}. {f}" for i, f in enumerate(merged))
        return bullets, len(merged)

    def _calculate_requirements_completeness(self, requirements: List[Dict[str, Any]]) -> float:
        """
        Calculate completeness score for formalized requirements.
        Based on presence of all ISO 29148 required fields.

        Side-effect: attaches a per-requirement ``completeness_score`` (float in
        [0.0, 1.0]) to each dict in ``requirements`` so the frontend can display
        a distinct score per card. The return value remains the document-level
        average for backward compatibility with existing callers.
        """
        if not requirements:
            return 0.0

        total_score = 0.0
        required_fields = ["title", "shall_statement", "rationale", "acceptance_criteria", "priority", "category"]

        for req in requirements:
            score = 0.0
            for field in required_fields:
                if field in req and req[field]:
                    # Check if acceptance_criteria has items if it's a list
                    if field == "acceptance_criteria" and isinstance(req[field], list):
                        if len(req[field]) > 0:
                            score += 1.0 / len(required_fields)
                    else:
                        score += 1.0 / len(required_fields)
            # Attach the per-requirement score to the dict so it survives
            # through the WebSocket payload to the frontend.
            req["completeness_score"] = score
            total_score += score

        completeness = total_score / len(requirements) if requirements else 0.0
        logger.info(f"Requirements completeness: {completeness:.1%}")
        return completeness

    def _attach_per_requirement_quality(
        self,
        requirements: List[Dict[str, Any]],
        smells: List[Any],
    ) -> float:
        """
        Attach a per-requirement ``quality_score`` derived from smell severity.

        Smells are produced against the raw input text and carry a ``location``
        (quoted phrase). Formalization rewrites wording (e.g. "must" → "shall"),
        so exact substring matching fails. Instead we use word-overlap: if ≥40%
        of a smell's meaningful tokens appear in a requirement's title+shall_statement,
        that smell is attributed to that requirement. Stopwords and modal verbs
        (must/shall/should) are excluded from tokens so rewriting doesn't break matching.

        The return value is the average quality score across all requirements
        — this is the new document-level cumulative shown in the feed footer.

        Notes:
        - ``smells`` may contain either ``RequirementSmellAnalysis`` model
          instances or dicts (``state["smells"]`` stores dumped dicts at
          line 402). Both shapes are handled.
        - Pure text matching — NO additional LLM calls.
        """
        if not requirements:
            return 0.0

        import re as _re

        def _tokens(text: str) -> set:
            """Meaningful word tokens — strip stopwords that differ between raw/formalized text."""
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                         "being", "have", "has", "had", "do", "does", "did", "will",
                         "would", "could", "should", "may", "might", "must", "shall",
                         "system", "to", "of", "in", "for", "on", "with", "at", "by",
                         "from", "up", "about", "into", "through", "during", "it",
                         "its", "that", "this", "and", "or", "but", "not", "no"}
            return {w for w in _re.findall(r"[a-z0-9]+", text.lower()) if w not in stopwords and len(w) > 2}

        # Normalize smell entries to a uniform (location_tokens, severity) shape.
        normalized_smells: List[Dict[str, Any]] = []
        for s in smells or []:
            if isinstance(s, dict):
                loc = s.get("location") or ""
                sev = float(s.get("severity", 0.0) or 0.0)
            else:
                loc = getattr(s, "location", "") or ""
                sev = float(getattr(s, "severity", 0.0) or 0.0)
            if not loc:
                continue
            normalized_smells.append({"tokens": _tokens(loc), "severity": sev})

        # Lowered from 0.4 → 0.2 (Bug 2): formalization rewrites wording, so
        # demanding 40% token overlap meant most smells failed to match any
        # requirement, leaving every quality_score at 1.0 even when the input
        # was riddled with smells.
        OVERLAP_THRESHOLD = 0.2

        # First pass: compute per-req matched severity sum.
        per_req_match: List[float] = []
        global_matched_total = 0.0
        for req in requirements:
            shall = (req.get("shall_statement") or "").lower()
            title = (req.get("title") or "").lower()
            req_tokens = _tokens(f"{title} {shall}")

            matched_severity_sum = 0.0
            for ns in normalized_smells:
                smell_tokens = ns["tokens"]
                if not smell_tokens:
                    continue
                overlap = len(smell_tokens & req_tokens) / len(smell_tokens)
                if overlap >= OVERLAP_THRESHOLD:
                    matched_severity_sum += ns["severity"]
            per_req_match.append(matched_severity_sum)
            global_matched_total += matched_severity_sum

        # Fallback distribution (Bug 2): if smells exist but NO requirement
        # matched any of them, the document still has known defects — penalize
        # all requirements by the average smell severity rather than leaving
        # every quality_score at 1.0.
        fallback_penalty = 0.0
        if normalized_smells and global_matched_total == 0.0:
            avg_severity = sum(ns["severity"] for ns in normalized_smells) / len(normalized_smells)
            fallback_penalty = avg_severity
            logger.info(
                f"Smell match fallback engaged: {len(normalized_smells)} smells but no "
                f"req matched. Distributing avg severity {avg_severity:.3f} across all "
                f"{len(requirements)} requirements."
            )

        total_quality = 0.0
        for req, matched_severity_sum in zip(requirements, per_req_match):
            effective = matched_severity_sum if matched_severity_sum > 0.0 else fallback_penalty
            per_req_smell_score = min(1.0, effective)
            quality_score = round(1.0 - per_req_smell_score, 4)
            # Clamp defensively — round of a negative could still slip in edge cases
            if quality_score < 0.0:
                quality_score = 0.0
            elif quality_score > 1.0:
                quality_score = 1.0
            req["quality_score"] = quality_score
            total_quality += quality_score

        average_quality = total_quality / len(requirements)
        logger.info(
            f"Per-requirement quality attached. avg_quality={average_quality:.3f} "
            f"across {len(requirements)} reqs (matched against {len(normalized_smells)} smells, "
            f"fallback_penalty={fallback_penalty:.3f})"
        )
        return average_quality


# Global agent instance
_agent = None


def get_agent() -> RequirementsAnalysisAgent:
    """Get or initialize the global agent instance."""
    global _agent
    if _agent is None:
        _agent = RequirementsAnalysisAgent()
    return _agent
