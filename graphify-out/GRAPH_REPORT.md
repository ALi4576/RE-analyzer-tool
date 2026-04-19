# Graph Report - f:/coding/RE_tool  (2026-04-19)

## Corpus Check
- Corpus is ~36,860 words - fits in a single context window. You may not need a graph.

## Summary
- 581 nodes · 1358 edges · 39 communities detected
- Extraction: 53% EXTRACTED · 47% INFERRED · 0% AMBIGUOUS · INFERRED: 641 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Agent Session Orchestration|Agent Session Orchestration]]
- [[_COMMUNITY_Requirements Export Pipeline|Requirements Export Pipeline]]
- [[_COMMUNITY_REST API & File Service|REST API & File Service]]
- [[_COMMUNITY_Architecture Rebuild Components|Architecture Rebuild Components]]
- [[_COMMUNITY_Agent State Management|Agent State Management]]
- [[_COMMUNITY_Context Injection Engine|Context Injection Engine]]
- [[_COMMUNITY_Audio Streaming Service|Audio Streaming Service]]
- [[_COMMUNITY_GPU Resource Manager|GPU Resource Manager]]
- [[_COMMUNITY_Frontend Audio Recording|Frontend Audio Recording]]
- [[_COMMUNITY_Environment Setup|Environment Setup]]
- [[_COMMUNITY_Transcription Engine|Transcription Engine]]
- [[_COMMUNITY_Frontend API Client|Frontend API Client]]
- [[_COMMUNITY_Latency Testing|Latency Testing]]
- [[_COMMUNITY_CLI Interface|CLI Interface]]
- [[_COMMUNITY_Configuration Settings|Configuration Settings]]
- [[_COMMUNITY_App Entry Point|App Entry Point]]
- [[_COMMUNITY_Logging Utils|Logging Utils]]
- [[_COMMUNITY_Requirement Input UI|Requirement Input UI]]
- [[_COMMUNITY_Frontend Helpers|Frontend Helpers]]
- [[_COMMUNITY_Backend Test Suite|Backend Test Suite]]
- [[_COMMUNITY_React App Root|React App Root]]
- [[_COMMUNITY_Loading Components|Loading Components]]
- [[_COMMUNITY_Notification Components|Notification Components]]
- [[_COMMUNITY_Requirement Viewer|Requirement Viewer]]
- [[_COMMUNITY_Analysis Results UI|Analysis Results UI]]
- [[_COMMUNITY_Clarification Panel UI|Clarification Panel UI]]
- [[_COMMUNITY_Header Component|Header Component]]
- [[_COMMUNITY_Requirement Card UI|Requirement Card UI]]
- [[_COMMUNITY_Smell Meter UI|Smell Meter UI]]
- [[_COMMUNITY_Waveform Visualizer UI|Waveform Visualizer UI]]
- [[_COMMUNITY_Requirement State Store|Requirement State Store]]
- [[_COMMUNITY_Workflow Test|Workflow Test]]
- [[_COMMUNITY_PostCSS Config|PostCSS Config]]
- [[_COMMUNITY_Tailwind Config|Tailwind Config]]
- [[_COMMUNITY_Vite Config|Vite Config]]
- [[_COMMUNITY_Vite Environment Types|Vite Environment Types]]
- [[_COMMUNITY_Components Index|Components Index]]
- [[_COMMUNITY_Requirement Feed|Requirement Feed]]
- [[_COMMUNITY_TypeScript Types|TypeScript Types]]

## God Nodes (most connected - your core abstractions)
1. `info()` - 84 edges
2. `RequirementAnalysisState` - 83 edges
3. `AnalysisStatus` - 81 edges
4. `ISORequirement` - 65 edges
5. `FormalizedRequirement` - 54 edges
6. `ExportResult` - 34 edges
7. `RequirementSmell` - 28 edges
8. `RequirementSmellAnalysis` - 28 edges
9. `ClarificationQuestion` - 28 edges
10. `RequirementsAnalysisAgent` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Get or initialize the global document reader service.` --uses--> `ContextInjectionPayload`  [INFERRED]
  services\reader_service.py → models\schemas.py
- `lifespan()` --calls--> `get_transcriber()`  [INFERRED]
  main.py → core\transcriber.py
- `lifespan()` --calls--> `get_agent()`  [INFERRED]
  main.py → core\agents.py
- `clarify_requirements()` --calls--> `info()`  [INFERRED]
  api\routes.py → main.py
- `upload_audio()` --calls--> `info()`  [INFERRED]
  api\routes.py → main.py

## Hyperedges (group relationships)
- **LangGraph Agent Pipeline Workflow** — retool_parse_input_node, retool_detect_smells_node, retool_analyze_logic_node, retool_generate_questions_node, retool_formalize_node, retool_export_ready_node [EXTRACTED 1.00]
- **GPU Inference Stack (RTX 4070 Super)** — retool_faster_whisper, retool_ollama_llm, retool_cuda_gpu, retool_vad_transcriber_py [EXTRACTED 1.00]
- **Real-Time Audio Ingestion Pipeline** — retool_websocket_handler, retool_stream_service_py, retool_audio_stream_buffer, retool_transcriber_py, retool_vad_transcriber_py [EXTRACTED 1.00]
- **Export Backend Integrations** — retool_exporter_py, retool_jira_exporter, retool_trello_exporter [EXTRACTED 1.00]
- **Session and GPU Resource Management** — retool_gpu_manager_py, retool_session_manager_py, retool_memory_saver [EXTRACTED 1.00]
- **React Frontend Component Set** — retool_requirement_input_tsx, retool_analysis_results_tsx, retool_clarification_panel_tsx, retool_zustand_store, retool_api_ts [EXTRACTED 1.00]
- **Core Service Modules** — retool_stream_service_py, retool_file_service_py, retool_reader_service_py [EXTRACTED 1.00]

## Communities

### Community 0 - "Agent Session Orchestration"
Cohesion: 0.06
Nodes (60): Run the analysis workflow.                  Args:             state: Initial, Resume workflow after user provides clarifications.                  Args:, Clean up session upload files after export.                  Args:, info(), Detailed system information., analyze_requirements(), websocket_stream(), AnalysisStatus (+52 more)

### Community 1 - "Requirements Export Pipeline"
Cohesion: 0.07
Nodes (47): ExportManager, get_export_manager(), JiraExporter, Export module for converting requirements to Jira/Trello tickets. Handles ticke, Format requirement as Jira ticket description., Map ISO priority to Jira priority., Export ISO requirements to Trello cards., Initialize Trello exporter. (+39 more)

### Community 2 - "REST API & File Service"
Cohesion: 0.06
Nodes (52): BaseModel, Enum, FileUploadService, get_file_service(), File upload service for handling PDF, Audio, and document uploads. Processes fi, Process audio file: transcribe to text.                  Args:             fi, Get or initialize the global file upload service., Manages file uploads with async processing.          Supported formats:     - (+44 more)

### Community 3 - "Architecture Rebuild Components"
Cohesion: 0.06
Nodes (55): AgentState TypedDict (LangGraph State Schema), Core Agents Module (core/agents.py), AnalysisResults Component (React), Logic Analyzer Agent Node, API Service Client (src/services/api.ts), Architecture Fix Plan (Critical Issues), AudioStreamBuffer (5-second PCM buffering), ClarificationPanel Component (React) (+47 more)

### Community 4 - "Agent State Management"
Cohesion: 0.11
Nodes (31): AgentState, get_agent(), Multi-Agent Orchestration using LangGraph. Implements the "Squad" logic with Hu, Convert state to dict if it's a Pydantic model., Parse and normalize input text., Detect requirement smells.                  Returns smells and calculates smel, LangGraph state schema for requirement analysis workflow., Determine if workflow should interrupt for human clarification. (+23 more)

### Community 5 - "Context Injection Engine"
Cohesion: 0.11
Nodes (20): ContextInjectionManager, get_context_manager(), Context Injection module for PDF/document processing. Enables ground truth veri, Create an enhanced prompt with context injection.         This is the key to gr, Smart extraction - detect file type and process accordingly., Retrieve cached context without re-extraction., Get or initialize the global context manager., Manages context extraction and injection from PDF documents.     This enables t (+12 more)

### Community 6 - "Audio Streaming Service"
Cohesion: 0.1
Nodes (16): AudioStreamBuffer, get_stream_service(), Real-time audio stream service for WebSocket-based audio processing. Handles PC, Force close a stream., Buffer for audio stream chunks.     Accumulates chunks and triggers transcripti, Initialize audio buffer.                  Args:             session_id: Sessi, Add audio chunk to buffer.                  Args:             audio_bytes: Ra, Real-time audio streaming and transcription.          Receives PCM audio chunk (+8 more)

### Community 7 - "GPU Resource Manager"
Cohesion: 0.11
Nodes (13): get_gpu_manager(), GPUResourceManager, GPU Resource Management and VRAM Optimization for RTX 4070 Super. Implements mo, Release a session slot.                  Args:             session_id: Sessio, Clear GPU cache to free memory., Get current GPU statistics., Get or initialize global GPU resource manager., Manages GPU resources for concurrent model inference.          Constraints: (+5 more)

### Community 8 - "Frontend Audio Recording"
Cohesion: 0.13
Nodes (4): AudioRecorder, WebSocketAudioStreamer, handleStartRecording(), handleStopRecording()

### Community 9 - "Environment Setup"
Cohesion: 0.21
Nodes (21): check_cuda(), check_ollama(), check_python_version(), create_directories(), create_env_file(), install_dependencies(), main(), print_error() (+13 more)

### Community 10 - "Transcription Engine"
Cohesion: 0.11
Nodes (12): Faster-Whisper based audio transcription module. Optimized for RTX 4070 Super w, get_vad_transcriber(), Voice Activity Detection (VAD) enabled transcriber with sliding window. Provide, Finalize transcription and return any remaining audio.         Call when stream, Detect if audio chunk is silence using energy-based VAD.                  Args, Transcribe current buffer contents.                  Args:             final:, Transcriber with Voice Activity Detection and sliding window buffering., Reset transcriber state for new session. (+4 more)

### Community 11 - "Frontend API Client"
Cohesion: 0.13
Nodes (3): APIClient, handleClarify(), handleExport()

### Community 12 - "Latency Testing"
Cohesion: 0.28
Nodes (8): main(), End-to-End Latency Test for Sentinel-RE. Measures latency from text input to re, Run comprehensive latency tests., Test REST endpoint latency for single requirement analysis.          Returns:, Test WebSocket streaming latency.     Streams text character by character and m, run_latency_tests(), test_rest_endpoint_latency(), test_websocket_streaming_latency()

### Community 13 - "CLI Interface"
Cohesion: 0.39
Nodes (7): main(), CLI utility for testing and managing the RE Tool., Test requirement analysis., test_analysis(), test_health(), test_status(), test_transcribe()

### Community 14 - "Configuration Settings"
Cohesion: 0.33
Nodes (4): Configuration package., Configuration and environment settings for the RE Tool backend., Application settings., Settings

### Community 15 - "App Entry Point"
Cohesion: 0.4
Nodes (3): lifespan(), Main FastAPI application for Multi-Agentic Requirements Engineering Tool.  Arc, Manage application startup and shutdown.     Initializes GPU-bound resources on

### Community 16 - "Logging Utils"
Cohesion: 0.4
Nodes (3): get_logger(), Logging configuration for the RE Tool backend., Get a configured logger instance.

### Community 17 - "Requirement Input UI"
Cohesion: 0.5
Nodes (2): handleDocumentUpload(), handleFileSelect()

### Community 18 - "Frontend Helpers"
Cohesion: 0.4
Nodes (0): 

### Community 19 - "Backend Test Suite"
Cohesion: 1.0
Nodes (2): print_result(), test_all()

### Community 20 - "React App Root"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "Loading Components"
Cohesion: 0.67
Nodes (0): 

### Community 22 - "Notification Components"
Cohesion: 0.67
Nodes (0): 

### Community 23 - "Requirement Viewer"
Cohesion: 0.67
Nodes (0): 

### Community 24 - "Analysis Results UI"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Clarification Panel UI"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Header Component"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Requirement Card UI"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Smell Meter UI"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Waveform Visualizer UI"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Requirement State Store"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Workflow Test"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "PostCSS Config"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Tailwind Config"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Vite Config"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Vite Environment Types"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Components Index"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Requirement Feed"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "TypeScript Types"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **102 isolated node(s):** `CLI utility for testing and managing the RE Tool.`, `Test requirement analysis.`, `Main FastAPI application for Multi-Agentic Requirements Engineering Tool.  Arc`, `Manage application startup and shutdown.     Initializes GPU-bound resources on`, `Detailed system information.` (+97 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Analysis Results UI`** (2 nodes): `AnalysisResults()`, `AnalysisResults.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Clarification Panel UI`** (2 nodes): `ClarificationPanel()`, `ClarificationPanel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Header Component`** (2 nodes): `Header()`, `Header.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Requirement Card UI`** (2 nodes): `getStatusBadge()`, `RequirementCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Smell Meter UI`** (2 nodes): `getColor()`, `SmellMeter.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Waveform Visualizer UI`** (2 nodes): `draw()`, `WaveformVisualizer.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Requirement State Store`** (2 nodes): `setupWebSocketListeners()`, `requirementStore.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Workflow Test`** (1 nodes): `test_workflow.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PostCSS Config`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tailwind Config`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vite Config`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Vite Environment Types`** (1 nodes): `vite-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Components Index`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Requirement Feed`** (1 nodes): `RequirementFeed.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TypeScript Types`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `info()` connect `Agent Session Orchestration` to `Requirements Export Pipeline`, `REST API & File Service`, `Agent State Management`, `Context Injection Engine`, `Audio Streaming Service`, `GPU Resource Manager`, `Transcription Engine`, `App Entry Point`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `AnalysisStatus` connect `Agent Session Orchestration` to `REST API & File Service`, `Agent State Management`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `RequirementAnalysisState` connect `Agent Session Orchestration` to `REST API & File Service`, `Agent State Management`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `info()` (e.g. with `analyze_requirements()` and `clarify_requirements()`) actually correct?**
  _`info()` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 80 inferred relationships involving `RequirementAnalysisState` (e.g. with `FastAPI routes for the RE Tool backend. Exposes REST and WebSocket endpoints.` and `Analyze raw requirements text.     Runs the full pipeline: parsing -> smell det`) actually correct?**
  _`RequirementAnalysisState` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 77 inferred relationships involving `AnalysisStatus` (e.g. with `FastAPI routes for the RE Tool backend. Exposes REST and WebSocket endpoints.` and `Analyze raw requirements text.     Runs the full pipeline: parsing -> smell det`) actually correct?**
  _`AnalysisStatus` has 77 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `ISORequirement` (e.g. with `AgentState` and `RequirementsAnalysisAgent`) actually correct?**
  _`ISORequirement` has 62 INFERRED edges - model-reasoned connections that need verification._