# Sentinel-RE Architecture Fix Plan

## Critical Issues Identified

### 1. **State Handshake & LangGraph Integration**
- **Issue**: RequirementAnalysisState not properly integrated with LangGraph StateGraph
- **Fix**: Use TypedDict for LangGraph and ensure state flows correctly through nodes
- **Impact**: All state-dependent operations fail without proper state schema

### 2. **WebSocket Handler Issues**
- **Issue**: StreamingAnalysisHandler references undefined `self.active_connections`
- **Fix**: Properly delegate to WebSocketManager or refactor class hierarchy
- **Impact**: Real-time streaming and chat features don't work

### 3. **Audio Streaming Pipeline**
- **Issue**: No proper sliding window transcription with partial/final results
- **Fix**: Implement VAD-based chunking with 500ms partial updates and 1.5s final threshold
- **Impact**: No real-time transcription support

### 4. **GPU Resource Management**
- **Issue**: No VRAM management or concurrent session limiting
- **Fix**: Add semaphore for max 3 concurrent sessions and VRAM monitoring
- **Impact**: OOM crashes on multiple concurrent streams

### 5. **State Persistence**
- **Issue**: MemorySaver configured but session retrieval not implemented
- **Fix**: Add checkpoint loading and session resumption logic
- **Impact**: Sessions lost on disconnect

## Implementation Order

1. Fix LangGraph StateGraph schema
2. Fix WebSocket handler architecture
3. Implement session persistence
4. Add streaming pipeline with VAD
5. Add GPU resource management
6. Optimize latency (target: < 2.5s)
