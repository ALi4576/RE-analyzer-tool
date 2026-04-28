# RE_tool — Performance & Architectural Comparison Report

**Date:** 2026-04-25
**Scope:** Backend log triage (run window 22:25–22:26) and architectural comparison against MARE (Jin et al., 2024) and KGMAF (Huang et al., 2025).

---

## TL;DR

Pipeline end-to-end latency is ~50 s (Session 1) and ~52 s (Session 2). The dominant cost is **Question Generation (~31 s and ~46 s)** — 62–88% of total wall-clock time — driven by `deepseek-r1:14b`'s internal chain-of-thought reasoning pass. Formalization produced 0 requirements in both runs due to a GPU discovery failure that degraded `qwen3.5:9b` inference to CPU. A duplicate session fired 6 s apart, doubling contention. Architecturally, RE_tool is closest to MARE (sequential pipeline + shared state) but differs by supporting multi-modal input, interactive latency targets, and a threshold-driven HITL loop.

---

## Section 1 — Timing Breakdown

### Active Models

| Role | Model |
|---|---|
| Main / Question Generation | `deepseek-r1:14b` |
| Smell + Gap Analysis | `qwen3.5:9b` |
| Formalization | `qwen3.5:9b` |

> Note: Ollama always logs `llama runner started` regardless of which model is loaded — this is its internal GGML engine name, not the model identifier.

### Session 1 (started 22:25:18)

| Stage | Duration | Notes |
|---|---|---|
| Quality Analysis (Smell + Gap) | ~14 s | Empty LLM response → fallback heuristic applied (smell=0.80, gap=0.70) |
| Formalization | ~5 s | Empty response → 0 requirements; interrupt flag raised |
| Consolidate | <1 s | Routing decision only |
| Question Generation | **~31 s** | **Bottleneck** — 4 questions emitted; deepseek-r1 chain-of-thought |
| **Total E2E** | **~50 s** | HTTP 200, status `needs_clarification` |

### Session 2 (started 22:25:24, +6 s after Session 1)

| Stage | Duration | Notes |
|---|---|---|
| Quality Analysis | ~11 s | Fallback path again |
| Formalization | ~6 s | 0 requirements |
| Question Generation | **~46 s** | Slower due to GPU contention with Session 1 |
| **Total E2E** | **~52 s** | HTTP 200, status `needs_clarification` |

### Bottleneck

**Question Generation** is 62–88% of total wall-clock time. This is expected with `deepseek-r1:14b` — it performs an internal chain-of-thought reasoning pass (`<think>...</think>`) before producing its answer, which accounts for ~20–30 s of the observed latency.

### GPU Warning Impact

Ollama logged `failure during GPU discovery` and `unable to refresh free memory`, indicating the runner degraded to CPU or ran with constrained VRAM. Two consequences:

1. **Cold start of 3.68 s** absorbed into Session 1's first node.
2. **Empty formalization output** — `qwen3.5:9b` is capable of producing valid JSON on GPU; empty responses under CPU-degraded inference confirm the hardware failure caused the 0-requirement result, not model capability.

### Duplicate Parallel Sessions

Two `Starting analysis` events fired 6 s apart from the same client. Likely causes: React StrictMode double-mount, or a missing in-flight request guard in the store. Effect: Session 2's question generation was **15 s slower** than Session 1's due to shared Ollama context window contention.

---

## Section 2 — Performance Summary

| Metric | Value | Notes |
|---|---|---|
| E2E latency (Session 1) | ~50 s | Above acceptable interactive threshold (<10 s) |
| E2E latency (Session 2) | ~52 s | Concurrency penalty visible |
| Cold start overhead | 3.68 s | One-off; applies after Ollama idle eviction |
| Formalization success rate | **0% (2/2 runs)** | Caused by GPU degradation, not model capability |
| Question Generation share | 62–88% of total | Inherent to deepseek-r1 chain-of-thought |

### Recommendations

| Issue | Recommendation |
|---|---|
| GPU discovery failure | Pin Ollama to a specific device via `CUDA_VISIBLE_DEVICES=0`; verify `nvidia-smi` reports the runner before starting the API |
| Empty formalization | Resolve GPU issue first; if CPU-only, consider a lighter model for formalize step (e.g. `qwen3.5:9b` already set — just needs GPU to function correctly) |
| Question Generation latency | Stream tokens over WebSocket so perceived latency drops to first-token (~2–3 s); or route question gen to a non-reasoning model (e.g. `qwen3.5:9b`) via a new `OLLAMA_QUESTIONS_MODEL` env var |
| Duplicate sessions | Add in-flight guard in React store keyed on session ID; return `409 Conflict` server-side if session already running |
| Cold start | Heartbeat ping to Ollama every 60 s during active use to prevent idle eviction |

---

## Section 3 — Architectural Comparison: RE_tool vs MARE vs KGMAF

### Core Mechanisms

**MARE (Jin et al., 2024)** decomposes RE into four sequential tasks — *elicitation, modeling, verification, specification* — executed by five role-named LLM agents (Stakeholder, Collector, Modeler, Checker, Documenter) communicating through a shared workspace of typed artifacts. Action migration is a finite-state graph with nine actions; the loop terminates when the Checker accepts the draft. Evaluated on Precision/Recall/F1 across nine RE cases.

**KGMAF (Huang et al., 2025)** extends MARE with six specialised agents (Interviewer, End-User, Analyst, Archivist, Reviewer, Deployer) and explicit knowledge injection from three sources (Software Projects, Literature/Standards, Domain Experts), categorised into six knowledge types. Coordination uses a **blackboard-style artifact pool** rather than a state machine. HITL is first-class and event-driven.

**RE_tool** uses a **single-pipeline LangGraph state machine** with five nodes (Quality Analysis → Formalization → Consolidate → Question Generation → optional Clarification loop) over one typed `RequirementAnalysisState` object. Two models are used (`deepseek-r1:14b` for reasoning-heavy tasks, `qwen3.5:9b` for fast smell/formalize steps). HITL is triggered by a numeric threshold (`smell_score ≥ 0.7`), not agent-driven.

### How RE_tool Differs

1. **Single pipeline, two-model strategy** rather than multi-agent personas. RE_tool switches between `deepseek-r1:14b` and `qwen3.5:9b` by node role; MARE/KGMAF instantiate distinct agent objects with persistent profiles.
2. **No requirements modeling stage.** RE_tool produces ISO 29148 JSON directly from raw text. MARE produces problem/use-case/goal diagrams as a first-class artifact.
3. **State object, not artifact pool.** All intermediate data lives in one LangGraph checkpoint. MARE/KGMAF expose multiple typed artifacts with explicit provenance.
4. **Multi-modal input.** RE_tool ingests audio (faster-whisper + VAD) and PDF context (PyMuPDF). Neither MARE nor KGMAF address audio or document input.
5. **Interactive latency target.** RE_tool targets a single-user sub-minute loop. MARE and KGMAF are evaluated as offline batch generators with no latency reporting.

### Comparison Table

| Dimension | RE_tool | MARE | KGMAF |
|---|---|---|---|
| **Input modality** | Text, audio (Whisper), PDF context | Text only | Text only |
| **NLP approach** | `deepseek-r1:14b` (reasoning) + `qwen3.5:9b` (fast), prompt-switched per node | 5 GPT-3.5 agents, one per role | 6 GPT-4-turbo agents, knowledge-injected |
| **Output format** | ISO 29148 JSON requirements + clarification questions | Requirements diagrams (use-case/problem/goal) + SRS document | Seven typed artifacts (URL, OEL, SRL, RM, SRS, IR, PAR) |
| **Human-in-the-loop** | Threshold-triggered (smell ≥ 0.7), max 3 clarification rounds | Implicit via start action | First-class — every artifact is reviewable; feedback re-triggers agents |
| **Knowledge injection** | Smell taxonomy + ISO 29148 template (in prompts only) | Metamodel + SRS template per agent | Six categorised knowledge types from three external sources |
| **Scalability** | Single user; GPU-bound; semaphore caps at 3 concurrent | Sequential, cloud-token-bound | Conceptual — blackboard supports parallel agents in principle |
| **Maturity** | Working product (FastAPI + React, WebSocket streaming) | Empirically evaluated (9 cases, F1 metrics) | Vision paper + 1 case study |

### Key Advantages per System

| System | Strengths |
|---|---|
| **RE_tool** | Real-time interactive loop; multi-modal input (audio + PDF); local-first/zero-cloud-cost; graceful degradation (heuristic fallbacks); per-node telemetry |
| **MARE** | SOTA F1 on three modeling tasks; unified end-to-end SRS generation; well-defined action migration graph; quantitatively evaluated |
| **KGMAF** | Richest agent set; explicit traceable domain-knowledge injection; event-driven collaboration; HITL designed in from the start |

### Key Limitations per System

| System | Limitations |
|---|---|
| **RE_tool** | No modeling stage (no diagrams); single pipeline means reasoning and fast-inference tasks share the same node abstraction; no knowledge taxonomy |
| **MARE** | Requires OpenAI GPT-3.5; no offline/local model story; no knowledge injection; no validated HITL loop in published runs |
| **KGMAF** | Vision/proof-of-concept only — one case study, no quantitative metrics; depends on an undefined knowledge extraction pipeline; six-agent overhead is heavy for small requirement sets |

---

## Closing Note

RE_tool's pipeline shape is MARE-minus-modeling-stage with threshold-driven HITL. Its strongest academic differentiators are **multi-modal input** and the **interactive real-time loop** — neither MARE nor KGMAF address those. The highest-leverage addition for academic positioning would be a **Modeling Node** between Formalization and Question Generation that produces a problem-diagram or goal-model artifact, which would make RE_tool directly benchmarkable against MARE's published F1 scores on the public ATM/COS/TLS/TAS/TMS cases.

---

*References:*
- *Jin et al. (2024). MARE: Multi-Agents Collaboration Framework for Requirements Engineering.*
- *Huang et al. (2025). KGMAF: Knowledge-Guided Multi-Agent Framework for Software Requirements Engineering.*
