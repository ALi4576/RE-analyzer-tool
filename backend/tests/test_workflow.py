import sys
import logging
from core.agents import RequirementsAnalysisAgent
from models.schemas import RequirementAnalysisState

# Suppress verbose logging
logging.basicConfig(level=logging.ERROR)

try:
    print("Initializing agent...")
    agent = RequirementsAnalysisAgent()
    
    print("Running analysis...")
    state = RequirementAnalysisState(
        session_id="test-001",
        input_text="The system shall allow users to login with email or password"
    )
    
    result = agent.analyze(state)
    
    print("\n" + "="*60)
    print("✅ SUCCESS - WORKFLOW COMPLETED!")
    print("="*60)
    print(f"Status: {result.get('status')}")
    print(f"Smell Score: {result.get('smell_score', 0):.2f}")
    print(f"Requirements Generated: {len(result.get('requirements', []))}")
    
    if result.get('requirements'):
        print("\nRequirements:")
        for req in result.get('requirements', []):
            print(f"  - {req.get('requirement_id', 'REQ-????')}: {req.get('title', 'N/A')}")
    
    print(f"\nResult state keys: {', '.join(result.keys())}")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
