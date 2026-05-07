# Sentinel-RE — Client Presentation Document
**Prepared for:** Client Review  
**Date:** April 2026  
**Prepared by:** Development Team  
**Audience:** Non-technical stakeholders

---
> **How to use this document:** Each section below maps to one slide in the presentation. The content is intentionally detailed so the designer has full context. Bullet points can be expanded into visuals, diagrams, or icons as appropriate.

---

## Slide 1 — Introduction

**Headline 1:** Requirements Engineering and Test Driven devolpment SoSe26.
**Headline 2:** Multi-Agentic AI Teams.
**Subtitle 1:** Submitted to Professor Henning Femmer
**Subtitle 2:** Presented by Ali Asad
---

## Slide 2 — Structure of Presentation (Table of contents)
1. Problem Statement / task
2. RE Methedology(Multi-Agentic AI Teams) brief introduction
3. Existing methods and their comparision
4. Current approach
5. Problems and limitations
6. Output and Results(SRS)
7. References
8. Discussion
---

## Slide 3 — Problem Statement / task
**Headline:** The core idea is to generate a tool that does our requirements documentation process for us. The tool has access to our backlog and is able to show us what is missing, ask the right questions and execute all the changes for us.

**Headline:** Stop writing requirements documents. Feed in whatever you already have — typed notes, a meeting recording, a PDF charter, or live speech — and get a professional industry level output.

Writing software requirements is one of the most error-prone parts of any project. Business analysts and product managers spend hours translating raw inputs — meeting notes, audio recordings, stakeholder emails, legacy specifications — into structured documents. And even then, requirements often come out vague, incomplete, or inconsistent. This project is being built to solve exactly this problem. The core idea is that **requirements engineering should be input-agnostic**: whatever form the raw material comes in, the system accepts it, analyses it, and formats it into professionally structured requirements without manual re-writing.

We assume that the system accepts four input modes, all of which produce the same structured output:
- **Typed or pasted text** — the primary input in the UI. A user can type a rough requirement, paste a chunk of meeting notes, or drop in content from an email thread. Analysis fires incrementally as text is entered.
- **Uploaded audio files** — pre-recorded interviews, workshop recordings, or voice memos (.mp3, .wav, .m4a, .ogg, .flac) are transcribed and analysed.
- **Live voice capture** — the user can speak into a microphone and have their words transcribed in real time. This is one input path among several, not the primary use case.
- **Uploaded documents (PDF / TXT)** — existing project charters, specifications, or scope documents are parsed and used either as the source material or as ground-truth context that every new requirement is cross-checked against.

Whichever input is used, the downstream pipeline is identical. 
<!-- The tool follows the **ISO 29148 standard**, an internationally recognised framework for writing software requirements. Every requirement it produces has a unique ID, a formal "shall" statement, a business rationale, measurable acceptance criteria, a priority level, and a category. -->

<!-- Beyond formatting, it also acts as a quality gate. It detects specific types of requirement problems — vague language, missing measurements, internal contradictions — and flags them before they become expensive mistakes in development. When something is too unclear to proceed, the AI pauses and asks the user targeted clarifying questions, much like a senior requirement engineer would in a meeting. -->

The end product of one session is a set of clean, formal requirements that push directly into the team's existing tools — with a single click, removing the manual copy-paste step that wastes hours every sprint.

---

## Slide 4 — Multi-Agent Systems — Core Concepts

> Sources: IBM (*What is a Multi-Agent System?*, *What is AI Agent Orchestration?*, *What is Multi-Agent Collaboration?*) and Google Cloud (*Guide to Multi-Agent Systems*)


## 1. What is a Single Agent?

A **single agent** is one autonomous AI that works entirely on its own. It perceives its environment, reasons, and acts independently to achieve a specific goal — with no interaction with other agents.

> *"Single-agent systems feature a single, autonomous entity working independently within its environment to achieve specific goals, without direct interaction with other agents. Think of a chess-playing AI that operates in isolation, analyzing the board and making decisions based on predefined rules or learned strategies."*
> — Google Cloud, Guide to Multi-Agent Systems

### When single agents work best

| Scenario | Why it fits |
|---|---|
| Well-defined problems | Clear rules, no collaboration needed |
| Centralized control | Simpler to build, lower maintenance cost |
| Predictable outcomes | Fraud detection, spam filtering, recommendations |

**Examples:** Chess AI, spam filter, fraud detector, product recommendation engine

---

## 2. What is a Multi-Agent System?

A **multi-agent system (MAS)** is when several autonomous AI agents — each with a specialized role — work together in a shared environment to solve problems too complex for any single agent.

> *"A multi-agent system consists of multiple artificial intelligence agents working collectively to perform tasks on behalf of a user or another system. Each agent within a MAS has individual properties but all agents behave collaboratively to lead to desired global properties."*
> — IBM, What is a Multi-Agent System?

### 3 Core Components of a MAS

| Component | Description |
|---|---|
| **Agents** | Active, decision-making entities — each has a role, tools, and a degree of autonomy |
| **Environment** | The shared space (virtual or physical) where agents work and interact |
| **Protocols** | The rules and languages agents use to communicate (e.g. JSON, FIPA ACL, KQML) |

> *"The distributed workload and specialized roles allow MAS to handle complex, dynamic, or large-scale challenges that would overwhelm a single agent."*
> — Google Cloud, Guide to Multi-Agent Systems

**Examples:** Warehouse robot fleets, customer service pipelines, AI coding teams, supply chain management

---

## Slide 5 — Agent Orchestration

## 3. What is Agent Orchestration?

**Agent orchestration** is the coordination layer that manages which agent does what, when, and in what order — like a conductor directing an orchestra.

> *"AI agent orchestration functions like a digital symphony. Each agent has a unique role and the system is guided by an orchestrator — either a central AI agent or framework — that manages and coordinates their interactions. The orchestrator helps synchronize these specialized agents, ensuring that the right agent is activated at the right time for each task."*
> — IBM, What is AI Agent Orchestration?

> *"Modern MAS operates on the principle of orchestration, where a complex task is broken down into a structured agentic workflow — like a project plan where different agents are assigned specific roles."*
> — Google Cloud, Guide to Multi-Agent Systems

### Types of Orchestration (IBM)

| Type | How it works | Best for |
|---|---|---|
| **Centralized** | One orchestrator agent is the "brain" — assigns tasks, makes final decisions | Consistent, predictable workflows |
| **Decentralized** | No single controller — agents communicate directly and reach consensus | Scalability and resilience |
| **Hierarchical** | Agents arranged in layers, like a command structure — senior agents manage junior ones | Complex, tiered workflows |

---

## 4. Single Agent vs. Multi-Agent

| Dimension | Single Agent | Multi-Agent System |
|---|---|---|
| **Structure** | One AI does everything | Multiple specialized AIs collaborate |
| **Complexity** | Simple to build and maintain | Complex to design and coordinate |
| **Cost** | Lower operational cost | Higher (especially with LLM API calls) |
| **Task type** | Focused, well-defined tasks | Dynamic, large-scale, multi-step tasks |
| **Communication** | No communication overhead | Agents pass messages and share results |
| **Fault tolerance** | Fails completely if it fails | One agent failing doesn't stop the rest |
| **Scalability** | Limited | Add more agents without breaking the system |

> *"Multi-agent collaboration provides numerous architectural, computational and operational benefits in contrast with other agentic architecture types, specifically a single-agent system — especially in environments that are highly complex, distributed and have privacy constraints."*
> — IBM, What is Multi-Agent Collaboration?

---

## Slide 6 — Multi-Agent Collaboration

## 5. Centralized vs. Decentralized

This refers to **how agents are controlled** and **how they share knowledge** within a MAS.

> *"In centralized networks, a central unit contains the global knowledge base, connects the agents and oversees their information. Agents in decentralized networks share information with their neighboring agents instead of a global knowledge base — the failure of one agent does not cause the overall system to fail."*
> — IBM, What is a Multi-Agent System?

### Side-by-Side Comparison

| Dimension | Centralized | Decentralized |
|---|---|---|
| **Control** | One central unit manages all agents | Agents self-organize and communicate peer-to-peer |
| **Knowledge** | Global knowledge base shared by all | Each agent only knows what its neighbors share |
| **Strength** | Easy communication, uniform knowledge | Robust, modular, fault tolerant |
| **Weakness** | Single point of failure — if center fails, all fails | Can produce conflicting or unpredictable behavior |
| **Scalability** | Harder to scale (bottleneck at center) | Easier to scale (no central dependency) |

---

## 6. How Do Multi-Agents Collaborate?

Collaboration is the core mechanism that makes MAS powerful. Agents don't just work in parallel — they perceive, reason, act, and communicate in a coordinated loop.

> *"Multi-agent orchestration allows agents, assistants and different data sources to collaborate — breaking down silos that separate teams and functions, enhancing knowledge sharing and speeding up decision-making."*
> — IBM, Inside the World of Multi-Agent Orchestration

### The Collaboration Loop

| Step | What happens |
|---|---|
| **1. Perceive** | Agents observe their surroundings and collect data — directly or by noticing changes in the shared environment |
| **2. Reason & decide** | An LLM acts as the agent's "brain," understanding intent and planning a course of action |
| **3. Act** | Agents carry out their planned actions — searching, writing, coding, calling APIs, updating databases |
| **4. Communicate** | Agents pass messages, share findings, or modify the shared environment for others to observe |
| **5. Shared memory** | A common memory store holds intermediate outputs and decisions so agents stay aware of each other's progress |
| **6. Iterate** | The flow orchestrator sequences tasks, handles errors, retries failed steps — agents can run simultaneously |

### IBM's Components Enabling Collaboration

- **Skill Registry** — lists each agent's capabilities and metadata so the system knows what each one can do
- **Intent Parser** — uses NLP to read a user's request and match it to the right agent skills
- **Flow Orchestrator** — handles task sequencing, branching, error handling, and retries
- **Shared Context & Memory Store** — a common space for data, intermediate outputs, and decisions across all agents

---

## References

1. IBM — *What is a Multi-Agent System?*
   https://www.ibm.com/think/topics/multiagent-system

2. IBM — *What is AI Agent Orchestration?*
   https://www.ibm.com/think/topics/ai-agent-orchestration

3. IBM — *What is Multi-Agent Collaboration?*
   https://www.ibm.com/think/topics/multi-agent-collaboration

4. IBM — *Inside the World of Multi-Agent Orchestration*
   https://www.ibm.com/think/insights/boost-productivity-efficiency-multi-agent-orchestration

5. Google Cloud — *Guide to Multi-Agent Systems (MAS)*
   https://cloud.google.com/discover/what-is-a-multi-agent-system

---




<!-- ## Slide 2 — What We've Built: The User Experience

**Headline:** From the moment you open the app, it just works — feed in whatever you have.

The frontend is a modern web application built in React and TypeScript, running in the browser. No installation is needed for the end user — they open the URL and choose how they want to provide input.

**The primary interface is a text area.** A user can type a requirement directly, paste a rough description from an email or meeting note, or drop in an entire block of raw text. As they type or paste, the system fires **incremental analysis** every time the character count crosses a new threshold — so results start appearing on screen before the user has finished composing their full thought. Hitting "Analyze" submits the complete text for a final pass.

Alongside the text input, the user can choose any of three alternative input modes:
- **Upload a pre-recorded audio file** (.mp3, .wav, .m4a, .ogg, .flac) — the file is transcribed on the GPU and the transcription is then analysed exactly as typed text would be.
- **Record live voice** — a microphone button begins capturing audio; a **live waveform visualiser** shows the system is actively listening, and transcribed text begins appearing on screen within one to two seconds of being spoken. The speech-to-text conversion happens in real time using a GPU-accelerated AI model called Faster-Whisper.
- **Upload a document (PDF / TXT)** — an existing project charter or specification can either be the source material for requirements extraction, or serve as ground-truth context that every new requirement is cross-checked against. When uploaded as context, the AI flags anything that contradicts the document or introduces new scope.

On the right-hand side of the screen, a **live requirement feed** builds up as input flows in. Each requirement is formatted into its own card showing the requirement ID (e.g. REQ-0001), the formal "shall" statement, acceptance criteria, priority (High / Medium / Low), and category (Functional / Non-Functional / Interface). The user watches their raw input — typed, spoken, or uploaded — turn into structured requirements in seconds.

A **quality meter** sits prominently on the screen, displaying a score for each requirement: Good, Warning, or Critical. This score is calculated by the AI based on how many quality issues it found. If the score is too low, the app automatically opens a **clarification panel** — an animated modal that pauses the session and presents specific follow-up questions. The user answers them, clicks continue, and the workflow resumes from exactly where it paused.

A **light and dark theme** follows the user's system preference automatically, and the export dialog lets the user review the final requirements before pushing them to Jira, Trello, or downloading a PDF.

---

## Slide 3 — What We've Built: The AI Agent Squad

**Headline:** Five specialised AI agents, each with one job — working as a team.

Rather than one general-purpose AI trying to do everything at once, Sentinel-RE uses a **multi-agent architecture** — a squad of five AI agents, each responsible for a specific task in the workflow. This design makes the system more reliable, more auditable, and easier to upgrade over time. The agents are orchestrated by a framework called LangGraph, which manages the order of operations, the state of each session, and the decision of when to pause and involve the human.

**Agent 1 — Quality Analyzer:** This agent receives the raw transcribed text and checks it against seven types of known requirement problems. These are: ambiguous language (e.g. "the system should be fast"), incomplete specifications (missing context), infeasible requirements (technically impossible or contradictory to known constraints), conflicting statements, unmeasurable criteria (no numbers or thresholds), vague scope (unclear system boundary), and missing rationale (no business reason given). Each problem found adds to a "smell score" between 0 and 1. This agent also scores any logical gaps in the requirement — missing preconditions, unstated assumptions, or unclear relationships to other requirements. Both scores are produced in a single AI call using a structured JSON format.

**Agent 2 — Formalizer:** Once the quality analysis is done, this agent rewrites the requirement in ISO 29148 format. It generates a unique ID, converts the loose spoken sentence into a formal "shall" statement, writes a business rationale, creates measurable acceptance criteria, assigns a priority and category, and links related requirements together via traceability fields. This is the agent responsible for the actual structured output the user sees on screen.

**Agent 3 — Consolidator:** This agent does not call the LLM. It merges the outputs from the Quality Analyzer and the Formalizer, then makes a binary decision: is the smell score above the threshold (currently set at 0.7 out of 1.0)? If yes, the workflow is interrupted and control is handed to the Clarifier. If no, the workflow proceeds to export.

**Agent 4 — Clarifier:** Only triggered when the Consolidator raises a flag, this agent generates targeted questions based specifically on the smells detected. If the requirement was flagged as "ambiguous" and "unmeasurable", the questions will be about clarifying the specific language and adding a number or threshold. These are not generic questions — they are contextually generated from the actual content of the requirement.

**Agent 5 — Export Ready:** The final agent simply marks the session as complete and ready for export. It sets a status flag that the frontend reads to enable the Jira / Trello export button.

---

## Slide 4 — What We've Built: The Technical Foundations

**Headline:** Built to be resilient, not just functional.

The backend is built on **FastAPI**, a modern Python web framework optimised for high-performance, asynchronous processing. This means the server can handle multiple users making requests at the same time without any one request blocking another. Audio is streamed over a **WebSocket connection**, which keeps a live bidirectional channel open between the browser and the server for the duration of the session — the same protocol used by real-time collaboration tools. Audio arrives at the server in five-second chunks, which is the minimum duration Faster-Whisper needs to produce accurate transcriptions. The five-second buffer is a deliberate design choice to balance transcription accuracy with perceived speed.

One of the more critical engineering decisions was the **Human-in-the-Loop checkpoint system**. When the Consolidator decides to interrupt, the entire workflow state is saved to a memory checkpoint using LangGraph's built-in checkpointer. The session is paused at exactly that point. When the user submits their clarification answers, the workflow resumes from the saved checkpoint — not from the beginning. This means no re-processing, no lost data, and no re-running expensive AI calls. This mechanism also powers **session recovery**: if the user's browser disconnects mid-session, reconnecting resumes the workflow from the last saved checkpoint.

The system also includes a **GPU resource manager** that uses an AsyncIO semaphore to cap the number of simultaneous active sessions at three. This prevents out-of-memory crashes on the GPU. The manager monitors VRAM usage in real time, issues warnings at 70% usage (approximately 8.6 GB out of 12 GB), and triggers critical alerts at 85% usage (approximately 10.4 GB). After each session completes, the GPU cache is automatically cleared to free memory for the next user.

All data flowing into the system is validated using **Pydantic schemas** — requirement text is capped at 50,000 characters, session IDs are capped at 50 characters, file paths are validated before any file system access, and file types and sizes are checked on upload before any processing begins. The entire application is packaged with a **Dockerfile and Docker Compose configuration**, meaning it can be deployed consistently on a local machine, a server, or a cloud environment without any environment-specific changes to the code.

---

## Slide 5 — How the AI Brain Works

**Headline:** Your requirements never leave your machine. Here is exactly how the AI works.

The AI model powering Sentinel-RE is **Llama 3**, a large language model developed by Meta and released as open source. It runs entirely on the local machine using a tool called **Ollama**, which manages downloading, loading, and serving the model on the GPU. There is no API key, no subscription, no data sent to OpenAI, Anthropic, Google, or any other cloud service. Every word the user speaks stays on the hardware in the room.

The model is loaded into GPU memory when the backend starts, and stays resident there for the life of the server process. This means the first request after startup has a cold-start cost, but every subsequent request is fast because the model is already in memory. The current configuration uses **Llama 3 with 4-bit quantisation** (a compression technique that reduces the model's memory footprint while preserving most of its accuracy), occupying approximately 8–9 GB of the 12 GB available on the RTX 4070 Super GPU.

For every requirement that comes in, the AI makes **exactly two passes**. The first pass sends the raw text to the Quality Analyzer agent, which returns a structured JSON object containing the list of detected smells, the smell score, and the logical gap score. Using a structured JSON response format means the output is predictable and machine-readable — the system does not need to parse free-form text to extract these values. The second pass sends the same text (plus any PDF context and any clarification answers the user provided) to the Formalizer agent, which returns the full ISO 29148 requirement as a structured object.

When a PDF document is uploaded, the system extracts the text using **PyMuPDF** and identifies key sections (headings, objectives, constraints) using a block-level analysis of the document structure. This extracted context is then prepended to every AI prompt as "ground truth", with an instruction to the model to flag any requirement that contradicts the document or introduces scope not mentioned in it. This is how the system catches scope creep and contradictions at the point of capture rather than at the point of review.

The **smell score threshold** is currently set at 0.7. This is configurable via the `.env` file. A score of 0.7 means the AI found enough quality issues that it does not trust the requirement to be formalised without human input. Lowering this threshold makes the system more permissive; raising it makes it more strict. This is a tuning decision that should be made based on real usage data from the client's team.

---

## Slide 6 — What Is Working Right Now

**Headline:** The full core workflow is built and connected — this is what you can see in a demo today.

The most important thing to communicate on this slide is that Sentinel-RE is **not a prototype or a proof of concept**. It is a working, integrated application where the frontend and backend are fully connected and communicating. None of the AI components are mocked or stubbed — the real Llama 3 model runs and produces real output, and the real Faster-Whisper model transcribes real audio.

All four input modes are operational and wired into the same analysis pipeline:

- **Typed / pasted text flow** works end to end. A user types or pastes into the input area and incremental analysis fires every 30 characters, with a final pass on submit. This is the fastest path from input to ISO-formatted card — no transcription step, just straight into the agent pipeline.
- **Audio file upload flow** works. The user selects a `.mp3`, `.wav`, `.m4a`, `.ogg`, or `.flac` file; the backend saves it, transcribes it with Faster-Whisper, and feeds the resulting text into the same analysis pipeline.
- **Live voice recording flow** works end to end. A user clicks the record button, speaks a requirement, and within one to two seconds of each five-second audio chunk, the transcribed text appears on screen. The browser's MediaRecorder API captures audio as WebM container chunks and streams them over the WebSocket to the backend, which hands them to Faster-Whisper running on the GPU.
- **Document upload flow (for context)** is wired into the UI and backend — the file is saved, PyMuPDF extracts the text, and the context manager caches it for injection into subsequent prompts. The end-to-end validation (uploaded doc → contradiction surfaced in a card) is still in the gap list.

The **analysis and card generation flow** works regardless of which input mode was used. Once enough text accumulates, the LangGraph workflow fires. The Quality Analyzer detects smells and scores the requirement. The Formalizer rewrites it in ISO 29148 format. The result appears on screen as a structured requirement card with all fields populated: ID, shall statement, rationale, acceptance criteria, priority, category. The quality meter updates to reflect the score.

The **clarification flow** works. When the smell score exceeds 0.7, the clarification panel opens automatically, displaying the questions generated by the Clarifier agent. The user can read and answer each question in the UI. On submission, the workflow resumes and produces an updated, improved requirement card.

The **theme system, waveform visualiser, PDF upload UI, and export confirmation dialog** are all built and functional in the browser. The application handles session management — generating a unique session ID on load, passing it through every API call and WebSocket message, and using it to scope all state, files, and checkpoints to that specific user session. The backend's GPU resource manager and session manager are both operational and enforcing the three-session limit.

---

## Slide 7 — What Has Not Yet Been Tested

**Headline:** We are being transparent. These are the gaps we need to close together.

Every item on this slide is something that is **built but not yet validated under real conditions**. This is not a list of broken things — it is a list of things we have not yet been able to verify because we need either real credentials, real data, or a structured testing session with the client.

**Document upload end-to-end:** The PDF upload component exists in the UI, the file service on the backend saves the file, and the context manager parses and caches the extracted text. However, we have not run a complete test where a user uploads a real project charter and then speaks a requirement that contradicts it, and verified that the contradiction is correctly surfaced in the UI. This specific chain — upload → parse → inject into prompt → contradiction detected → shown to user — needs to be tested as a single flow.

**Jira and Trello export:** The integration code is written for both platforms. The Jira exporter uses the official `jira` Python library to create Story issues with custom fields mapped to the ISO requirement fields. The Trello exporter uses the `trello` Python library to create cards on a specified board and list. However, we have not yet tested either integration against a real Jira project or a real Trello board using live API credentials. We do not yet know whether the field mappings align with the client's Jira custom fields or whether the API token permissions are configured correctly.

**No automated test suite:** There are currently zero unit tests, integration tests, or end-to-end tests. The system has been tested manually, but there is no regression safety net. This means that if a future code change breaks the smell detection logic or the ISO formatter, the breakage will not be caught automatically.

**Authentication and access control:** The application currently has no login, no session tokens, and no access control. Any user who can reach the URL can use the system. This is acceptable for a closed internal pilot but is a security gap for any wider deployment.

**End-to-end latency benchmarking:** The target latency is under 2.5 seconds from the end of a spoken requirement to the moment a formatted requirement card appears on screen. This target has not been formally measured. The system feels fast in development, but we have not instrumented the pipeline to record timestamps at each stage and produce a latency distribution across multiple runs.

**Audio edge cases:** We have tested with clear English speech in a quiet environment. We have not tested with heavy accents, fast speech, background noise, very long recordings, or audio recorded on a low-quality microphone. Faster-Whisper is robust, but the impact of audio quality on transcription accuracy — and therefore on requirement quality — is an unknown.

**ISO 29148 accuracy validation:** The AI produces "shall" statements and structured requirement fields, but we have not had a requirements engineering expert review the output and score it against the ISO 29148 standard. The 90% accuracy target in the project requirements has not been verified.

---

## Slide 8 — Performance and Response Time

**Headline:** The system is fast by design — but we need your real workload to measure it properly.

The performance architecture of Sentinel-RE was designed around the RTX 4070 Super GPU, which provides 12 GB of VRAM. The GPU runs two AI models simultaneously: Faster-Whisper (occupying approximately 2.5 GB) and Ollama with Llama 3 (occupying approximately 8–9 GB, using 4-bit quantisation). Together, they leave roughly 0.5 to 1.5 GB of headroom for buffers and spikes, which the GPU resource manager protects by issuing warnings before the system gets into dangerous territory.

**Transcription speed** is the fastest part of the pipeline. Faster-Whisper on CUDA can process approximately one minute of audio in one to two seconds of wall-clock time. Because the system buffers audio in five-second chunks, the user experiences transcription appearing on screen within two to three seconds of finishing a sentence. This is a good experience in practice — the text "catches up" with natural speech pauses.

**AI analysis speed** is the slower part of the pipeline. Each requirement goes through two LLM calls (quality analysis and formalisation). On the RTX 4070 Super, Llama 3 generates at approximately 50–100 tokens per second. A typical requirement analysis response is 200–400 tokens. This puts the LLM processing time at roughly two to four seconds per requirement, meaning the combined pipeline (transcription + analysis + card rendering) is expected to be in the two to five second range depending on requirement complexity.

The **2.5-second end-to-end target** is achievable but has not been formally measured. It is more likely to be met for short, clear requirements and less likely for long, complex ones. We recommend running a structured latency test using real requirement examples from the client's domain before committing this as a Service Level Agreement.

| Metric | Target | Current Status |
|---|---|---|
| Audio transcription time | 1–2 seconds per minute of audio | Consistent in dev testing |
| End-to-end latency (speech → card) | Under 2.5 seconds | Not formally benchmarked |
| Concurrent active sessions | Up to 3 per machine | Implemented, not load-tested |
| VRAM stability under sustained use | Stable with auto-cleanup | Cleanup implemented, not stress-tested |
| Export to Jira / Trello | Under 1 second per requirement | Code written, not tested live |

A key factor affecting performance is the **Ollama model choice**. The system is currently configured to use Llama 3 (a larger, more accurate model). If response time is a higher priority than ISO accuracy, the system can be reconfigured to use a smaller model such as Phi-3 Mini, which is significantly faster but produces less precise output. This is a configurable setting and does not require code changes. The right choice depends on the client's tolerance for speed vs. accuracy, which is something we need to discuss.

---

## Slide 9 — Known Limitations and What Could Be Improved

**Headline:** We know what the gaps are. Here is how we would close them.

**No multi-user collaboration:** Each session in Sentinel-RE is tied to a single user. Two people cannot co-author requirements in the same session simultaneously, and there is no concept of a shared workspace or team view. This is by design for the initial version — it was not in the original scope — but it is an important limitation for any team where requirements gathering is a collaborative activity. Adding this would require a shared session model, real-time state broadcasting to multiple WebSocket clients, and a conflict resolution strategy.

**No requirement history or versioning:** Once a requirement is exported to Jira or Trello, the app does not keep a local record of it. There is no history view, no diff between versions, no way to see what was changed between sessions, and no audit trail within the application itself. The only record is whatever Jira or Trello stores. This will become a problem for teams that iterate on requirements over multiple sessions and need to track how a requirement evolved. A requirements database with version control would address this.

**No user authentication or access control:** The application is currently open — any user who knows the URL can start a session and push requirements. Adding authentication (OAuth2 via the organisation's SSO, or a simple API key) is not complex but is a prerequisite for any production deployment where requirements contain confidential information.

**No operator or admin view:** There is no dashboard for whoever is administering the system. You cannot see how many sessions have run, how long they lasted, how many requirements were generated, or what the GPU utilisation looked like over time. Structured logs are written to `backend/logs/re_tool.log`, but they are raw text files. A proper admin view would surface this as a dashboard and alert on anomalies.

**Hardware dependency on a GPU:** In the current setup, Sentinel-RE must run on a machine with an NVIDIA GPU (RTX 4070 Super or equivalent, with at least 10–11 GB of available VRAM). This is a significant constraint. If the machine with the GPU is unavailable, the system cannot run. Cloud deployment (e.g. on an AWS instance with a GPU, or using Azure OpenAI for the LLM) would remove this dependency and allow access from anywhere, but would introduce hosting costs and — depending on the model used — would mean requirement text leaving the local network.

**No domain fine-tuning of the LLM:** The Llama 3 model we are using is a general-purpose model. It has not been trained on the client's domain language, acronyms, internal terminology, or requirement patterns. This means the first batch of requirements it produces may use slightly different phrasing or categorise things differently than a domain expert would expect. Fine-tuning the model on a set of example requirements from the client's domain would significantly improve the accuracy and style of the output, but requires a curated dataset and additional compute.

---

## Slide 10 — Open Questions for the Client (Part 1)

**Headline:** We cannot make these decisions without you. Let's work through them.

These questions are not rhetorical — each one has a direct impact on what the next phase of development looks like. We have grouped them by theme to make the conversation easier to navigate.

---

### Deployment and Hosting

**1. Should Sentinel-RE run on your own hardware (on-premises), or do you want it hosted in the cloud?**
Right now, the entire system — including the AI models — runs on a single physical machine with an NVIDIA GPU. This means your requirement data never leaves that machine. Cloud deployment would mean anyone on your team could access it from a browser anywhere in the world, but it introduces hosting costs and may mean requirement text passing through a cloud environment. Which matters more to you: local data control or anywhere-access?

**2. If on-premises, who owns running and maintaining the machine it runs on?**
The system needs to be on a machine that stays on, has the GPU driver and Ollama installed, and is accessible on the network. Does your organisation have an IT team who would own this, or does this fall to the development team?

**3. If cloud, what is the acceptable cloud provider?**
Not all organisations are permitted to use all cloud providers. Do you have a preferred or mandated provider — for example, AWS, Azure, Google Cloud, or a private data centre?

---

### Data Privacy and Compliance

**4. Do you have regulatory or legal requirements around where your data can be stored or processed?**
Some industries (defence, healthcare, finance, government) have strict rules about data sovereignty. For example, GDPR in Europe or internal data classification policies may restrict where requirement text can go. We need to know this before making any cloud decisions.

**5. Is it acceptable for requirement content to be processed by a cloud-based LLM at any point?**
Today, Llama 3 runs locally and no data leaves the machine. If we were to switch to a cloud LLM for performance (e.g. Claude or GPT-4), requirement text would be sent to a third-party API. Is that acceptable to your organisation, and if so, under what conditions?

**6. Who is the data owner of the requirements generated by Sentinel-RE?**
Is it the organisation, the individual user, or the project? This matters for retention, export, and deletion policies.

---

### Budget and Scope

**7. What is the expected budget range for the next phase of development?**
We need to understand whether the next phase is a short validation sprint, a longer hardening phase, or a full production rollout. These have very different cost profiles. Having a rough range — even a broad one — lets us prioritise accordingly.

**8. Is Sentinel-RE intended to be a long-term internal product, or a one-off tool for a specific project?**
If it is a long-term product, investments in authentication, versioning, admin dashboards, and fine-tuning make sense. If it is for a single project, we should focus only on what is needed to get through that project reliably.

---

## Slide 11 — Open Questions for the Client (Part 2)

**Headline:** Continued — Integrations, Users, Acceptance, and Timeline.

---

### Integrations and Export

**9. Do your teams currently use Jira, Trello, or another project management tool?**
Sentinel-RE currently has export integrations for both Jira and Trello. If your team uses something else — Notion, Linear, Azure DevOps, ServiceNow, Asana — the integration would need to be built. Some of these have straightforward APIs; others are more complex.

**10. Can you provide us with API credentials and a test project or board for the Jira or Trello integration?**
We have the integration code written, but we have not yet connected it to a live environment. To complete and validate the export flow, we need read/write API credentials and a sandbox project we can safely push test tickets to without affecting real work.

**11. Are there any specific custom fields in your Jira instance that Sentinel-RE requirements should map to?**
Different Jira configurations have different custom fields — for example, "Business Value", "Epic Link", "Acceptance Criteria" as a custom field, or internal project codes. We need to know your Jira schema to make sure the exported tickets look right from day one.

---

### Users and Scale

**12. How many people do you expect to use Sentinel-RE, and across how many teams?**
The current system is capped at three concurrent sessions per machine. If you have a large team or expect high simultaneous usage, we either need more powerful hardware or a cloud deployment with horizontal scaling. Understanding the expected user count shapes the infrastructure decision.

**13. Will all users be in the same physical location, or distributed across offices and time zones?**
If users are in different locations, a local-only deployment creates access problems. This reinforces the cloud vs. on-premises question and helps us think about latency and availability.

**14. Do you need multiple users to be able to work on the same set of requirements simultaneously — for example, during a workshop?**
Real-time collaboration is not currently built. If your team runs requirement workshops where multiple people are contributing at the same time, this becomes a priority feature.

---

### Acceptance Criteria and Testing

**15. What does "done" look like for you — what is the minimum the system must do for you to consider it production-ready?**
We want to align on this explicitly before the next phase begins. Is it: export a requirement to Jira that a developer can act on without editing? Produce output that a BA signs off as ISO 29148 compliant? Process a full one-hour requirements session without errors? Help us define the finish line.

**16. Can you provide a set of real example requirements — spoken or written — that we can use to test and calibrate the system?**
Testing with synthetic examples only tells us so much. Using your actual domain language, your actual requirement patterns, and your actual document formats will reveal gaps that test data cannot. Even 10–15 real examples would be enormously valuable.

**17. Who on your side will be conducting the acceptance testing, and what sign-off process do you follow?**
Knowing this shapes how we structure the handover. If it is a formal UAT process with sign-off documentation, we will prepare it differently than if it is a senior stakeholder doing a one-hour walkthrough.

**18. What would be the output of the system?**
ISO compliant format, user stories, usecase, UML, flow charts, state diagram.


**19. Does the system only automates the process or it should check for quality of requirements against some criteria?**

**20. Who is going to use the system like Product managers, testers, developers.**

**21. What are the external systems it is going to interact with i.e MS Teams, MS office suite, Jira, existing databases?**

**22. Does every session be saved or after generating requirements it would auto delete?**

---

### Timeline and Priorities

**23. If we could only complete three more things before the pilot starts, what would they be?**
We have a list of outstanding work: end-to-end document upload testing, Jira/Trello integration testing, authentication, automated tests, latency benchmarking, and load testing. We cannot do all of them in parallel with unlimited urgency. Tell us what matters most and we will sequence accordingly.

**24. Is there a fixed deadline — tied to a project kickoff, an internal presentation, an audit, or a board review — that we should be aware of?**
A hard deadline changes everything about prioritisation. We need to know about it now, not the week before.

---

## Closing Slide — Where We Stand

**Headline:** A working product, an honest gap list, and the path forward is a shared decision.

Sentinel-RE is a fully integrated, working application. The core workflow — speak a requirement, get a formatted ISO 29148 card, answer clarifying questions, push to Jira — is operational and demonstrable today. The AI runs privately on local hardware, the backend handles concurrent sessions with GPU safety guardrails, and the frontend is a polished, production-quality interface built in React.

The gap list in this document is not a list of things that are broken. It is a list of things that have been built but not yet verified under real conditions with real data. Closing those gaps is the work of the next phase — and most of it is validation, integration testing, and tuning, not rebuilding.

What the development team cannot decide unilaterally is the direction of that next phase. The answers to the open questions in this presentation determine whether we focus on cloud deployment or on-premises hardening, whether we build authentication next or tackle collaboration, and whether we fine-tune the AI model on your domain or ship it general-purpose and iterate. These are business decisions, not engineering decisions.

The request to the client is simple: come out of this meeting with answers to the ten most important questions, and the team will have a clear, prioritised plan for what comes next within 48 hours.

---

*Document prepared by the Sentinel-RE development team. April 2026.*  
*Total slides: 12 | Intended audience: Non-technical client stakeholders*  
*Designer note: UI screenshots are available from the live application running at localhost:3000. The five-agent diagram on Slide 3 is a strong candidate for an icon-based visual. The performance table on Slide 8 can become an infographic with traffic-light status indicators.* -->
