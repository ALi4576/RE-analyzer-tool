"""
Multi-Agent Orchestration using LangGraph.
Implements the "Squad" logic with Human-in-the-Loop pattern for requirements analysis.
"""
import asyncio
from typing import Dict, Any, List, TypedDict, Literal
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
        # Initialize LLM for analysis nodes (smell, logic, parse)
        self.llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.OLLAMA_TEMPERATURE,
            format="json",
            request_timeout=25,  # prevent hung requests from blocking a GPU slot indefinitely
        )
        # Low-temperature LLM for deterministic ISO 29148 formalization
        self.formalize_llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.OLLAMA_FORMALIZE_TEMPERATURE,
            format="json",
            request_timeout=25,
        )
        
        # Initialize state persister
        self.checkpointer = MemorySaver()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("RequirementsAnalysisAgent initialized")
    
    def _build_workflow(self):
        """Build LangGraph workflow for requirements analysis."""
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("parse_input", self._parse_input_node)
        workflow.add_node("detect_smells", self._detect_smells_node)
        workflow.add_node("analyze_logic", self._analyze_logic_node)
        workflow.add_node("formalize", self._formalize_node)
        workflow.add_node("consolidate", self._consolidate_results_node)
        workflow.add_node("generate_questions", self._generate_questions_node)
        workflow.add_node("export_ready", self._export_ready_node)
        
        # SCRIBE MODE: Sequential processing to avoid concurrent writes
        # Parse -> detect_smells and analyze_logic and formalize can run in sequence
        # but we use consolidate to merge their outputs before interrupt decision
        workflow.add_edge("parse_input", "detect_smells")
        workflow.add_edge("detect_smells", "analyze_logic")
        workflow.add_edge("analyze_logic", "formalize")
        workflow.add_edge("formalize", "consolidate")
        
        # Consolidate decides whether to interrupt based on smell score
        workflow.add_conditional_edges(
            "consolidate",
            self._should_interrupt,
            {
                True: "generate_questions",
                False: "export_ready",
            },
        )
        
        workflow.add_edge("generate_questions", END)  # Wait for user input
        workflow.add_edge("export_ready", END)
        
        # Set entry point
        workflow.set_entry_point("parse_input")
        
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
            # Convert Pydantic model to dict for LangGraph
            state_dict: AgentState = {
                "session_id": state.session_id,
                "input_text": state.input_text,
                "context_docs": [doc.model_dump() if hasattr(doc, 'model_dump') else doc for doc in (state.context_docs or [])],
                "status": state.status.value if hasattr(state.status, 'value') else str(state.status),
                "interrupt_needed": False,
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

            state_dict: AgentState = {
                "session_id": session_id,
                "input_text": existing.values.get("input_text", ""),
                "context_docs": existing.values.get("context_docs", []),
                "status": "clarified",
                "interrupt_needed": False,
                "user_clarifications": merged_clarifications,
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
        
        smell_prompt = f"""
Analyze this requirement text for common requirement smells:
- Ambiguous language (vague, imprecise)
- Incomplete specifications (missing details)
- Infeasible requirements (impossible to implement)
- Conflicting statements
- Unmeasurable criteria (no metrics)
- Scope creep indicators
- Missing business rationale

Input: {input_text}

For each smell found, rate severity 0-1 and suggest fix.
Format as JSON with fields: [{{\"type\": \"...\", \"severity\": 0.8, \"location\": \"...\", \"recommendation\": \"...\"}}]
"""
        
        smells_response = self.llm.invoke(smell_prompt)
        
        if not smells_response:
            logger.error("Ollama returned empty response for smells")
    
        # Parse LLM response to extract smells
        smells = self._parse_smell_response(smells_response, input_text)
        
        if not smells_response:
            logger.error("Ollama returned empty response for smells")
        
        # Calculate overall smell score
        smell_score = sum(s.severity for s in smells) / len(smells) if smells else 0.0
        
        logger.info(f"Smell detection complete. Score: {smell_score:.2f}, Smells found: {len(smells)}")
        
        state["smells"] = smells
        state["smell_score"] = smell_score
        
        return state
    
    def _should_interrupt(self, state: AgentState) -> bool:
        """
        Determine if workflow should interrupt for human clarification.

        Triggers when smell score OR logical gap score exceeds its threshold.
        """
        smell_score = state.get("smell_score", 0.0)
        logical_gap_score = state.get("logical_gap_score", 0.0)

        smell_trigger = smell_score >= settings.SMELL_SCORE_THRESHOLD
        gap_trigger = logical_gap_score >= settings.LOGICAL_GAP_THRESHOLD
        should_interrupt = smell_trigger or gap_trigger

        logger.info(
            f"Interrupt check: smell={smell_score:.2f}(>={settings.SMELL_SCORE_THRESHOLD}={smell_trigger}), "
            f"gap={logical_gap_score:.2f}(>={settings.LOGICAL_GAP_THRESHOLD}={gap_trigger}), "
            f"interrupt={should_interrupt}"
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
        
        logic_prompt = f"""
Analyze the logical structure of these requirements:

{input_text}

Identify:
1. Logical gaps (missing components)
2. Contradictions
3. Unclear dependencies
4. Missing acceptance criteria

Rate overall logical consistency 0-1.
"""
        
        logic_analysis = self.llm.invoke(logic_prompt)
        logical_gap_score = self._extract_score(logic_analysis)
        
        logger.info(f"Logic analysis complete. Gap score: {logical_gap_score:.2f}")
        
        state["logical_gap_score"] = logical_gap_score
        state["logic_analysis"] = logic_analysis
        
        return state
    
    def _generate_questions_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clarification questions for interruption."""
        logger.info("Executing: Question Generation Node")
        
        state = self._ensure_dict(state)
        input_text = state.get("input_text", "")
        smells = state.get("smells", [])
        
        questions_prompt = f"""
Based on these requirement quality issues, generate focused clarification questions:

Issues found:
{str(smells[:3])}

Input: {input_text}

Generate 2-3 specific questions to clarify ambiguities.
Format as JSON: [{{\"question_id\": \"q1\", \"question\": \"...\", \"context\": \"...\", \"required_clarity\": [\"...\"]}}]
"""
        
        questions_response = self.llm.invoke(questions_prompt)
        questions = self._parse_questions_response(questions_response)
        
        logger.info(f"Generated {len(questions)} clarification questions")
        
        state["clarification_questions"] = questions
        
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
        
        # Build clarifications
        clarifications_text = ""
        if clarification_questions:
            clarifications_text = "\n".join([
                f"Q: {q.get('question', '')}\nA: {state.get('user_clarifications', {}).get(q.get('question_id', ''), '')}"
                for q in clarification_questions
            ])
        
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

{context_header}{context_text if context_text else ''}

{clarifications_header}{clarifications_text if clarifications_text else ''}

TASK: If the input contains multiple requirements, requests, or features (including compound or multi-part sentences), split them into separate ISO 29148 compliant requirements. Each distinct user need or feature should become its own requirement in the output array.

ISO 29148 REQUIREMENTS:
1. Each requirement MUST use imperative "shall" language
2. Requirements must be testable/verifiable
3. Include clear title, shall statement, rationale, and acceptance criteria
4. Prioritize based on business impact
5. Categorize as Functional/Non-functional/Interface

OUTPUT FORMAT (JSON array):
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
            state["formalized"] = {
                "total_requirements": len(valid_requirements),
                "completeness_score": self._calculate_requirements_completeness(valid_requirements),
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
        # reading state (API endpoints, WebSocket) see the correct value.
        smell_score = state.get("smell_score", 0.0)
        logical_gap_score = state.get("logical_gap_score", 0.0)
        interrupt_needed = (
            smell_score >= settings.SMELL_SCORE_THRESHOLD
            or logical_gap_score >= settings.LOGICAL_GAP_THRESHOLD
        )
        state["interrupt_needed"] = interrupt_needed

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

        except Exception as e:
            logger.warning(f"Error parsing smell response: {str(e)}")
            smells.append(RequirementSmellAnalysis(
                smell_type=RequirementSmell.AMBIGUOUS,
                severity=0.5,
                location=original_text[:50],
                recommendation="Please clarify the requirement",
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
    
    def _calculate_requirements_completeness(self, requirements: List[Dict[str, Any]]) -> float:
        """
        Calculate completeness score for formalized requirements.
        Based on presence of all ISO 29148 required fields.
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
            total_score += score
        
        completeness = total_score / len(requirements) if requirements else 0.0
        logger.info(f"Requirements completeness: {completeness:.1%}")
        return completeness


# Global agent instance
_agent = None


def get_agent() -> RequirementsAnalysisAgent:
    """Get or initialize the global agent instance."""
    global _agent
    if _agent is None:
        _agent = RequirementsAnalysisAgent()
    return _agent
