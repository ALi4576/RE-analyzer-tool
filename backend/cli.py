"""
CLI utility for testing and managing the RE Tool.
"""

import argparse
import json
import asyncio
from pathlib import Path
import httpx

BASE_URL = "http://localhost:8000/api"


async def test_health():
    """Test API health."""
    print("Testing API health...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ API is healthy: {json.dumps(data, indent=2)}")
                return True
    except Exception as e:
        print(f"✗ API health check failed: {e}")
    return False


async def test_transcribe(audio_file: str):
    """Test transcription."""
    print(f"Testing transcription with {audio_file}...")
    
    if not Path(audio_file).exists():
        print(f"✗ File not found: {audio_file}")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/transcribe",
                json={
                    "file_path": audio_file,
                    "language": "en"
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Transcription successful!")
                print(f"  Text length: {data['text_length']} chars")
                print(f"  Text preview: {data['text'][:100]}...")
                return True
    except Exception as e:
        print(f"✗ Transcription failed: {e}")
    
    return False


async def test_analysis(text: str):
    """Test requirement analysis."""
    print(f"Testing analysis with: {text[:50]}...")
    
    try:
        session_id = "test-session"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/analyze",
                json={
                    "session_id": session_id,
                    "text": text,
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Analysis successful!")
                print(f"  Smell score: {data['analysis_summary']['smell_score']:.2f}")
                print(f"  Issues found: {data['analysis_summary']['issues_found']}")
                print(f"  Interrupt needed: {data['interrupt_needed']}")
                return True
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
    
    return False


async def test_status():
    """Get system status."""
    print("Getting system status...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/status")
            if response.status_code == 200:
                data = response.json()
                print("✓ System status:")
                print(json.dumps(data, indent=2))
                return True
    except Exception as e:
        print(f"✗ Failed to get status: {e}")
    
    return False


async def main():
    """Main CLI."""
    parser = argparse.ArgumentParser(
        description="RE Tool CLI - Test and manage the backend"
    )
    parser.add_argument(
        "command",
        choices=["health", "status", "transcribe", "analyze"],
        help="Command to run"
    )
    parser.add_argument(
        "--file",
        help="Audio file for transcription"
    )
    parser.add_argument(
        "--text",
        help="Text for analysis"
    )
    
    args = parser.parse_args()
    
    if args.command == "health":
        await test_health()
    
    elif args.command == "status":
        await test_status()
    
    elif args.command == "transcribe":
        if not args.file:
            print("Error: --file required for transcribe command")
            return
        await test_transcribe(args.file)
    
    elif args.command == "analyze":
        if not args.text:
            print("Error: --text required for analyze command")
            return
        await test_analysis(args.text)


if __name__ == "__main__":
    asyncio.run(main())
