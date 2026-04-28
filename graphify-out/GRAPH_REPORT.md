# Graph Report - F:\coding\RE_tool  (2026-04-25)

## Corpus Check
- 57 files · ~123,858 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 704 nodes · 1867 edges · 73 communities detected
- Extraction: 37% EXTRACTED · 63% INFERRED · 0% AMBIGUOUS · INFERRED: 1170 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]

## God Nodes (most connected - your core abstractions)
1. `RequirementAnalysisState` - 157 edges
2. `AnalysisStatus` - 130 edges
3. `ISORequirement` - 123 edges
4. `FormalizedRequirement` - 86 edges
5. `info()` - 80 edges
6. `RequirementSmell` - 70 edges
7. `RequirementSmellAnalysis` - 70 edges
8. `ClarificationQuestion` - 70 edges
9. `ExportResult` - 66 edges
10. `RequirementsAnalysisAgent` - 41 edges

## Surprising Connections (you probably didn't know these)
- `RequirementAnalysisState` --calls--> `high_smell_state()`  [INFERRED]
  F:\coding\RE_tool\backend\models\schemas.py → F:\coding\RE_tool\backend\tests\test_clarification_flow.py
- `RequirementAnalysisState` --calls--> `low_smell_state()`  [INFERRED]
  F:\coding\RE_tool\backend\models\schemas.py → F:\coding\RE_tool\backend\tests\test_clarification_flow.py
- `lifespan()` --calls--> `get_agent()`  [INFERRED]
  F:\coding\RE_tool\backend\main.py → F:\coding\RE_tool\backend\core\agents.py
- `info()` --calls--> `formalize_requirements()`  [INFERRED]
  F:\coding\RE_tool\backend\main.py → F:\coding\RE_tool\backend\api\routes.py
- `info()` --calls--> `export_requirements()`  [INFERRED]
  F:\coding\RE_tool\backend\main.py → F:\coding\RE_tool\backend\api\routes.py

## Hyperedges (group relationships)
- **LangGraph Agent Pipeline Workflow** — retool_parse_input_node, retool_detect_smells_node, retool_analyze_logic_node, retool_generate_questions_node, retool_formalize_node, retool_export_ready_node [EXTRACTED 1.00]
- **GPU Inference Stack (RTX 4070 Super)** — retool_faster_whisper, retool_ollama_llm, retool_cuda_gpu, retool_vad_transcriber_py [EXTRACTED 1.00]
- **Real-Time Audio Ingestion Pipeline** — retool_websocket_handler, retool_stream_service_py, retool_audio_stream_buffer, retool_transcriber_py, retool_vad_transcriber_py [EXTRACTED 1.00]
- **Export Backend Integrations** — retool_exporter_py, retool_jira_exporter, retool_trello_exporter [EXTRACTED 1.00]
- **Session and GPU Resource Management** — retool_gpu_manager_py, retool_session_manager_py, retool_memory_saver [EXTRACTED 1.00]
- **React Frontend Component Set** — retool_requirement_input_tsx, retool_analysis_results_tsx, retool_clarification_panel_tsx, retool_zustand_store, retool_api_ts [EXTRACTED 1.00]
- **Core Service Modules** — retool_stream_service_py, retool_file_service_py, retool_reader_service_py [EXTRACTED 1.00]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (75): FileUploadService, get_file_service(), File upload service for handling PDF, Audio, and document uploads. Processes fi, Process audio file: transcribe to text.                  Args:             fi, Process document file: extract and cache context.                  Args:, Clean up session upload files after export.                  Args:, Get or initialize the global file upload service., Manages file uploads with async processing.          Supported formats:     - (+67 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (109): AgentState, Multi-Agent Orchestration using LangGraph. Implements the "Squad" logic with Hu, Build LangGraph workflow for requirements analysis.          Pipeline (2 LLM c, Parse LLM response into RequirementSmellAnalysis objects., Calculate completeness score for formalized requirements.         Based on pres, Attach a per-requirement ``quality_score`` derived from smell severity., Extract a 0-1 score from LLM response, preferring labeled values., Parse LLM formalization response into requirement dicts. (+101 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (92): BaseModel, ExportManager, get_export_manager(), JiraExporter, PdfExporter, Export module for converting requirements to Jira/Trello tickets. Handles ticke, Format requirement as Jira ticket description., Format requirement as Jira ticket description. (+84 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (20): get_formalizer(), ISO29148Formalizer, ISO 29148 Compliance Formatter. Transforms messy requirements into formally com, Export formalized requirements as JSON., Export formalized requirements as dictionary., Extract requirement title from text., Create formal "shall" statement.         ISO requires explicit testable stateme, Converts analyzed requirements into ISO/IEC 29148 standard format.          IS (+12 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (18): RequirementsAnalysisAgent, agent(), _build_fresh_agent(), high_smell_state(), low_smell_state(), _make_llm_side_effect(), Tests for the smell-detection → interrupt → clarification flow.  Uses unittest.m, After resume, question IDs must match the interrupted run — no regeneration. (+10 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (8): APIClient, handleClarify(), handleExport(), handleDrop(), handleFile(), handleInputChange(), validate(), handleFileSelect()

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (22): get_agent(), get_patches(), get_requirement_store(), merge(), patch(), In-memory overlay store for requirement field patches.  The LangGraph checkpoint, Record field-level overrides for a single requirement within a session.      Fie, Return the full patch map for a session, or an empty dict. (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (19): ContextInjectionManager, get_context_manager(), Context Injection module for PDF/document processing. Enables ground truth veri, Create an enhanced prompt with context injection.         This is the key to gr, Smart extraction - detect file type and process accordingly., Retrieve cached context without re-extraction., Get or initialize the global context manager., Manages context extraction and injection from PDF documents.     This enables t (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (14): get_session_manager(), Session Manager for state persistence and recovery. Uses LangGraph MemorySaver, End a session and save final state.                  Args:             sessio, Manages session lifecycle and persistence.     - Creates new sessions     - Re, Remove expired sessions.                  Returns:             Number of sess, Get number of active sessions., Get all active sessions., Get or initialize global session manager. (+6 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (4): AudioRecorder, WebSocketAudioStreamer, handleStartRecording(), handleStopRecording()

### Community 10 - "Community 10"
Cohesion: 0.21
Nodes (21): check_cuda(), check_ollama(), check_python_version(), create_directories(), create_env_file(), install_dependencies(), main(), print_error() (+13 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (11): get_vad_transcriber(), Voice Activity Detection (VAD) enabled transcriber with sliding window. Provide, Finalize transcription and return any remaining audio.         Call when stream, Detect if audio chunk is silence using energy-based VAD.                  Args, Transcribe current buffer contents.                  Args:             final:, Transcriber with Voice Activity Detection and sliding window buffering., Reset transcriber state for new session., Get or initialize VAD transcriber. (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.28
Nodes (8): main(), End-to-End Latency Test for Sentinel-RE. Measures latency from text input to re, Run comprehensive latency tests., Test REST endpoint latency for single requirement analysis.          Returns:, Test WebSocket streaming latency.     Streams text character by character and m, run_latency_tests(), test_rest_endpoint_latency(), test_websocket_streaming_latency()

### Community 13 - "Community 13"
Cohesion: 0.39
Nodes (7): main(), CLI utility for testing and managing the RE Tool., Test requirement analysis., test_analysis(), test_health(), test_status(), test_transcribe()

### Community 14 - "Community 14"
Cohesion: 0.33
Nodes (4): Configuration package., Configuration and environment settings for the RE Tool backend., Application settings., Settings

### Community 15 - "Community 15"
Cohesion: 0.4
Nodes (3): get_logger(), Logging configuration for the RE Tool backend., Get a configured logger instance.

### Community 16 - "Community 16"
Cohesion: 0.6
Nodes (3): priorityVariant(), RequirementCard(), statusForScore()

### Community 17 - "Community 17"
Cohesion: 0.4
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 0.4
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (2): cssVar(), draw()

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (2): PyMuPDF PDF Extraction Library, Python Dependencies (requirements.txt)

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (2): Human-in-the-Loop (HITL) Pattern, Rationale: HITL interrupt threshold (smell score >= 0.7)

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): Manage application startup and shutdown.     Initializes GPU-bound resources on

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (1): Detailed system information.

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): High-performance audio transcription using Faster-Whisper.

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (1): Initialize Whisper model with GPU optimization.

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (1): Transcribe an audio file to text.                  Args:             file_pat

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (1): Transcribe a single audio chunk from a stream.         Used for real-time proce

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): Transcribe with segment timestamps for synchronization.                  Args:

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): Get or initialize the global transcriber instance.

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Initial WebSocket stream request.

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): Analysis of requirement smells.

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Question to ask user for clarification.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): WebSocket payload for interrupting analysis.

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): ISO 29148 compliant requirement.

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Response from requirement analysis.

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Result of exporting requirements.

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Context data injected from PDF.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Audio chunk from WebSocket stream.

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): State model for LangGraph requirement analysis workflow.

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Validate uploaded file.                  Args:             file: File to vali

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Process audio file: transcribe to text.                  Args:             fi

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Process document file: extract and cache context.                  Args:

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Clean up session upload files after export.                  Args:

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Get or initialize the global file upload service.

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Multi-Agentic Requirements Engineering Tool (Sentinel-RE)

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): ISO 29148 Compliance Standard

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): PDF Context Injection (Ground Truth)

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): CUDA GPU Acceleration (RTX 4070 Super)

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Requirement Smell Detection

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Requirement Smell Types (ambiguous, incomplete, infeasible, etc.)

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Architecture Fix Plan (Critical Issues)

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): Rationale: 5-second audio buffer window

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Rationale: Max 3 concurrent sessions via semaphore

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Rationale: VAD dual-trigger (500ms partial, 1.5s silence final)

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): Rationale: Singleton GPU-bound models loaded once

## Knowledge Gaps
- **139 isolated node(s):** `CLI utility for testing and managing the RE Tool.`, `Test requirement analysis.`, `Main FastAPI application for Multi-Agentic Requirements Engineering Tool.  Arc`, `Manage application startup and shutdown.     Initializes GPU-bound resources on`, `Detailed system information.` (+134 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 23`** (2 nodes): `AnalysisResults()`, `AnalysisResults.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `Header()`, `Header.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `RequirementFeed.tsx`, `SkeletonCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `RequirementViewer.tsx`, `handleExport()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `SmellMeter.tsx`, `resolveTier()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `requirementStore.ts`, `setupWebSocketListeners()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `PyMuPDF PDF Extraction Library`, `Python Dependencies (requirements.txt)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `Human-in-the-Loop (HITL) Pattern`, `Rationale: HITL interrupt threshold (smell score >= 0.7)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `test_workflow.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `vite-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Loading.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `Manage application startup and shutdown.     Initializes GPU-bound resources on`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `Detailed system information.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `High-performance audio transcription using Faster-Whisper.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `Initialize Whisper model with GPU optimization.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `Transcribe an audio file to text.                  Args:             file_pat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `Transcribe a single audio chunk from a stream.         Used for real-time proce`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `Transcribe with segment timestamps for synchronization.                  Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `Get or initialize the global transcriber instance.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Initial WebSocket stream request.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `Analysis of requirement smells.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Question to ask user for clarification.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `WebSocket payload for interrupting analysis.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `ISO 29148 compliant requirement.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Response from requirement analysis.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Result of exporting requirements.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Context data injected from PDF.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Audio chunk from WebSocket stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `State model for LangGraph requirement analysis workflow.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Validate uploaded file.                  Args:             file: File to vali`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Process audio file: transcribe to text.                  Args:             fi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Process document file: extract and cache context.                  Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Clean up session upload files after export.                  Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Get or initialize the global file upload service.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Multi-Agentic Requirements Engineering Tool (Sentinel-RE)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `ISO 29148 Compliance Standard`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `PDF Context Injection (Ground Truth)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `CUDA GPU Acceleration (RTX 4070 Super)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Requirement Smell Detection`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Requirement Smell Types (ambiguous, incomplete, infeasible, etc.)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Architecture Fix Plan (Critical Issues)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `Rationale: 5-second audio buffer window`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Rationale: Max 3 concurrent sessions via semaphore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Rationale: VAD dual-trigger (500ms partial, 1.5s silence final)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Rationale: Singleton GPU-bound models loaded once`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `info()` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 11`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Why does `RequirementAnalysisState` connect `Community 1` to `Community 0`, `Community 8`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `APIClient` connect `Community 5` to `Community 9`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 154 inferred relationships involving `RequirementAnalysisState` (e.g. with `FastAPI routes for the RE Tool backend. Exposes REST and WebSocket endpoints.` and `Analyze raw requirements text.     Runs the full pipeline: parsing -> smell det`) actually correct?**
  _`RequirementAnalysisState` has 154 INFERRED edges - model-reasoned connections that need verification._
- **Are the 126 inferred relationships involving `AnalysisStatus` (e.g. with `WebSocketManager` and `StreamingAnalysisHandler`) actually correct?**
  _`AnalysisStatus` has 126 INFERRED edges - model-reasoned connections that need verification._
- **Are the 120 inferred relationships involving `ISORequirement` (e.g. with `AgentState` and `RequirementsAnalysisAgent`) actually correct?**
  _`ISORequirement` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `FormalizedRequirement` (e.g. with `FastAPI routes for the RE Tool backend. Exposes REST and WebSocket endpoints.` and `Analyze raw requirements text.     Runs the full pipeline: parsing -> smell det`) actually correct?**
  _`FormalizedRequirement` has 83 INFERRED edges - model-reasoned connections that need verification._