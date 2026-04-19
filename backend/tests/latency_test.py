"""
End-to-End Latency Test for Sentinel-RE.
Measures latency from text input to receiving formalized requirements.

Target: < 2.5 seconds per PRD requirements.
"""
import asyncio
import json
import time
import statistics
from typing import List, Dict, Any
import aiohttp
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/api/ws/stream"
SESSION_ID_PREFIX = "latency_test_"

# Test requirements
TEST_REQUIREMENTS = [
    "The system shall allow users to upload PDF documents for context injection",
    "The application shall transcribe audio in real-time with less than 500ms latency",
    "Requirements shall be formatted according to ISO 29148 standard",
    "The system shall detect requirement ambiguities and request clarification",
    "Users should be able to export requirements to Jira",
]

# Result tracking
latency_results: Dict[str, List[float]] = {
    "input_to_analysis": [],
    "analysis_to_formalization": [],
    "total_latency": [],
}


async def test_rest_endpoint_latency(test_text: str, session_id: str) -> Dict[str, float]:
    """
    Test REST endpoint latency for single requirement analysis.
    
    Returns:
        Dict with 'input_to_response' latency in milliseconds
    """
    endpoint = f"{BACKEND_URL}/api/analyze"
    
    payload = {
        "text": test_text,
        "session_id": session_id,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            async with session.post(endpoint, json=payload) as response:
                result = await response.json()
                end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            
            return {
                "status": "success",
                "latency_ms": latency_ms,
                "result": result,
            }
    
    except Exception as e:
        print(f"❌ REST endpoint error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": 0,
        }


async def test_websocket_streaming_latency(
    test_text: str, session_id: str
) -> Dict[str, Any]:
    """
    Test WebSocket streaming latency.
    Streams text character by character and measures time to first analysis update.
    
    Returns:
        Dict with streaming latency metrics
    """
    try:
        async with aiohttp.ClientSession() as session:
            ws_url = f"{WEBSOCKET_URL}/{session_id}"
            
            async with session.ws_connect(ws_url) as ws:
                start_time = time.time()
                first_analysis_time = None
                analysis_count = 0
                
                # Stream text chunks (simulating real-time input)
                chunk_size = 50
                for i in range(0, len(test_text), chunk_size):
                    chunk = test_text[i:i+chunk_size]
                    
                    message = {
                        "type": "text_chunk",
                        "data": chunk,
                        "is_final": False,
                    }
                    
                    await ws.send_json(message)
                    
                    # Give backend time to process
                    await asyncio.sleep(0.1)
                    
                    # Check for messages
                    try:
                        msg = await ws.receive_json(timeout=0.5)
                        
                        if first_analysis_time is None and msg.get("type") == "analysis_update":
                            first_analysis_time = time.time()
                            analysis_count += 1
                        
                        if msg.get("type") == "interrupt":
                            print(f"  - Received interrupt request with {len(msg.get('clarification_questions', []))} questions")
                
                    except asyncio.TimeoutError:
                        continue
                
                # Send finalize
                await ws.send_json({"type": "finalize"})
                
                # Wait for final results
                final_time = time.time()
                try:
                    final_msg = await ws.receive_json(timeout=2.0)
                    if final_msg.get("type") == "analysis_update":
                        final_time = time.time()
                
                except asyncio.TimeoutError:
                    pass
                
                total_latency_ms = (final_time - start_time) * 1000
                time_to_first_analysis_ms = (
                    (first_analysis_time - start_time) * 1000
                    if first_analysis_time else total_latency_ms
                )
                
                return {
                    "status": "success",
                    "time_to_first_analysis_ms": time_to_first_analysis_ms,
                    "total_latency_ms": total_latency_ms,
                    "analysis_count": analysis_count,
                }
    
    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": 0,
        }


async def run_latency_tests():
    """Run comprehensive latency tests."""
    print("\n" + "="*70)
    print("SENTINEL-RE END-TO-END LATENCY TEST")
    print("="*70)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Target Latency: < 2500ms (2.5s per PRD)")
    print(f"Test Requirements: {len(TEST_REQUIREMENTS)}")
    print("="*70 + "\n")
    
    # Check backend health
    print("🔍 Checking backend health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    print("✅ Backend is running\n")
                else:
                    print(f"❌ Backend returned status {response.status}")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {str(e)}")
        print(f"   Make sure the backend is running on {BACKEND_URL}")
        return
    
    # Run tests
    test_results = []
    
    print("📊 Running REST Endpoint Tests...")
    print("-" * 70)
    
    for i, requirement in enumerate(TEST_REQUIREMENTS, 1):
        session_id = f"{SESSION_ID_PREFIX}rest_{i}"
        print(f"\nTest {i}/5: {requirement[:50]}...")
        
        result = await test_rest_endpoint_latency(requirement, session_id)
        
        if result["status"] == "success":
            latency_ms = result["latency_ms"]
            latency_results["input_to_analysis"].append(latency_ms)
            
            status_icon = "✅" if latency_ms < 2500 else "⚠️ "
            print(f"  Latency: {latency_ms:.0f}ms {status_icon}")
            
            test_results.append({
                "test": f"REST_{i}",
                "latency_ms": latency_ms,
                "passed": latency_ms < 2500,
            })
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
    
    # Calculate REST statistics
    if latency_results["input_to_analysis"]:
        print("\n" + "-" * 70)
        print("REST ENDPOINT RESULTS:")
        rest_times = latency_results["input_to_analysis"]
        print(f"  Average: {statistics.mean(rest_times):.0f}ms")
        print(f"  Median:  {statistics.median(rest_times):.0f}ms")
        print(f"  Min:     {min(rest_times):.0f}ms")
        print(f"  Max:     {max(rest_times):.0f}ms")
        print(f"  Stdev:   {statistics.stdev(rest_times) if len(rest_times) > 1 else 0:.0f}ms")
        
        passed = sum(1 for t in rest_times if t < 2500)
        print(f"  Pass Rate: {passed}/{len(rest_times)} ({100*passed//len(rest_times)}%)")
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if latency_results["input_to_analysis"]:
        avg_latency = statistics.mean(latency_results["input_to_analysis"])
        target_latency = 2500
        
        if avg_latency < target_latency:
            print(f"✅ LATENCY TARGET MET: {avg_latency:.0f}ms < {target_latency}ms")
        else:
            print(f"⚠️  LATENCY ABOVE TARGET: {avg_latency:.0f}ms > {target_latency}ms")
        
        print(f"\nLatency Distribution:")
        for i, t in enumerate(latency_results["input_to_analysis"], 1):
            pct = 100 * t / target_latency
            bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
            print(f"  Test {i}: {t:6.0f}ms [{bar}] {pct:5.0f}%")
    
    print("\n" + "="*70)


async def main():
    """Main entry point."""
    try:
        await run_latency_tests()
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    print("\n🚀 Starting Sentinel-RE Latency Test Suite...")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    asyncio.run(main())
