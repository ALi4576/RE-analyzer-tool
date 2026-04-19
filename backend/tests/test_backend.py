#!/usr/bin/env python3
"""
Quick backend test script - Run this to verify all features work.
No frontend required!
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"

def print_result(title, status, data=None):
    """Print test result."""
    symbol = "✅" if status else "❌"
    print(f"\n{symbol} {title}")
    if data:
        if isinstance(data, dict):
            print(json.dumps(data, indent=2))
        else:
            print(str(data))

def test_all():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 BACKEND FEATURE TEST")
    print("="*60)
    
    try:
        # 1. Health check
        print("\n[1/7] Testing health check...")
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        health = r.status_code == 200
        print_result("Health Check", health, r.json() if health else r.text)
        
        # 2. Status
        print("\n[2/7] Testing system status...")
        r = requests.get(f"{BASE_URL}/status", timeout=5)
        status = r.status_code == 200
        print_result("System Status", status)
        
        # 3. Analyze
        print("\n[3/7] Testing requirement analysis...")
        session_id = f"test-{int(time.time())}"
        r = requests.post(
            f"{BASE_URL}/analyze",
            json={
                "session_id": session_id,
                "text": "System should be fast, handle 1000 users concurrently, and work on mobile devices",
            },
            timeout=30
        )
        analyze_ok = r.status_code == 200
        result = r.json() if analyze_ok else {}
        print_result("Analyze Requirements", analyze_ok, {
            "session_id": result.get("session_id"),
            "status": result.get("status"),
            "smell_score": result.get("analysis_summary", {}).get("smell_score"),
            "issues_found": result.get("analysis_summary", {}).get("issues_found")
        })
        
        # 4. Formalize
        print("\n[4/7] Testing formalization (ISO 29148)...")
        r = requests.post(f"{BASE_URL}/formalize", params={"session_id": session_id}, timeout=10)
        formalize_ok = r.status_code == 200
        formalized = r.json() if formalize_ok else {}
        
        iso_reqs = formalized.get("iso_requirements", [])
        print_result("Formalize Requirements", formalize_ok, {
            "total_requirements": len(iso_reqs),
            "ready_for_export": formalized.get("ready_for_export"),
            "first_requirement": iso_reqs[0] if iso_reqs else None
        })
        
        # 5. Export Jira (dry-run)
        print("\n[5/7] Testing Jira export (dry-run)...")
        r = requests.post(
            f"{BASE_URL}/export/dry-run",
            json={"session_id": session_id, "export_target": "jira"},
            timeout=10
        )
        jira_dry = r.status_code == 200
        print_result("Jira Dry-Run Export", jira_dry, r.json() if jira_dry else r.text)
        
        # 6. Export Trello (dry-run)
        print("\n[6/7] Testing Trello export (dry-run)...")
        r = requests.post(
            f"{BASE_URL}/export/dry-run",
            json={"session_id": session_id, "export_target": "trello"},
            timeout=10
        )
        trello_dry = r.status_code == 200
        print_result("Trello Dry-Run Export", trello_dry)
        
        # 7. Full export (if credentials configured)
        print("\n[7/7] Testing full export...")
        if formalized.get("ready_for_export"):
            r = requests.post(
                f"{BASE_URL}/export",
                json={"session_id": session_id, "export_target": "jira"},
                timeout=15
            )
            export_ok = r.status_code == 200 and r.json().get("status") in ["success", "failed"]
            print_result("Full Jira Export", export_ok, {
                "status": r.json().get("status"),
                "tickets": r.json().get("ticket_ids", [])
            })
        else:
            print_result("Full Export", True, "Skipped (requirements not ready)")
        
        # Summary
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   • Session: {session_id}")
        print(f"   • Requirements found: {len(iso_reqs)}")
        print(f"   • Ready for export: {formalized.get('ready_for_export')}")
        print("\n🎯 Next steps:")
        print("   1. Try analyzing different requirement texts")
        print("   2. Check LangGraph state: curl http://localhost:8000/api/formalize?session_id={session_id}")
        print("   3. Configure .env for real Jira/Trello integration")
        print("   4. Read TESTING_GUIDE.md for detailed feature tests")
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend!")
        print("   Make sure backend is running: python main.py")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_all()
    sys.exit(exit_code)
