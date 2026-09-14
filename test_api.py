import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    
    payload = json.dumps(data).encode("utf-8") if data else None
    
    try:
        with urllib.request.urlopen(req, data=payload) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body.startswith("{") or res_body.startswith("[") else res_body
    except urllib.error.HTTPError as e:
        res_body = e.read().decode("utf-8")
        return e.code, res_body
    except Exception as e:
        return 500, str(e)

def run_tests():
    print("=== CAMPUSPREP AI ENDPOINT VERIFICATION ===")

    # 1. Health Check
    status, body = make_request(f"{BASE_URL}/api/v1/health")
    print(f"[1/6] GET /api/v1/health -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    assert body.get("status") == "healthy", "Health check status invalid"
    print("      Health status:", body)

    # 2. Get Companies
    status, body = make_request(f"{BASE_URL}/api/v1/companies")
    print(f"[2/7] GET /api/v1/companies -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    companies = body.get("companies", [])
    assert len(companies) >= 4, f"Expected at least 4 companies, found {len(companies)}"
    print(f"      Loaded {len(companies)} company tracks: {[c['slug'] for c in companies]}")

    # 3. Get Courses
    status, body = make_request(f"{BASE_URL}/api/v1/courses")
    print(f"[3/7] GET /api/v1/courses -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    categories = body.get("categories", [])
    assert len(categories) == 4, f"Expected 4 course categories, found {len(categories)}"
    print(f"      Loaded {len(categories)} course categories: {[cat['category'] for cat in categories]}")

    # 3. Resume Scan
    resume_payload = {
        "resume_text": "Experienced engineer skilled in Data Structures and Algorithms (DSA), Python, SQL, Virtual Memory, and REST APIs.",
        "target_company": "zoho"
    }
    status, body = make_request(f"{BASE_URL}/api/v1/resumes/scan", method="POST", data=resume_payload)
    print(f"[3/6] POST /api/v1/resumes/scan -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    assert "ats_match_percentage" in body, "ATS score missing"
    print(f"      ATS Match Score: {body['ats_match_percentage']}%, Target: {body['target_company']}")

    # 4. Initiate Interview Session
    init_payload = {
        "company_slug": "zoho",
        "domain": "DSA"
    }
    status, body = make_request(f"{BASE_URL}/api/v1/interviews/sessions/initiate", method="POST", data=init_payload)
    print(f"[4/6] POST /api/v1/interviews/sessions/initiate -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    session_id = body.get("session_id")
    question_id = body.get("question", {}).get("id")
    assert session_id is not None and question_id is not None, "Session or question ID missing"
    print(f"      Initiated Session: {session_id}, Question ID: {question_id}")
    print(f"      Prompt: {body['question']['prompt']}")

    # 5. Execute Turn
    turn_payload = {
        "session_id": session_id,
        "question_id": question_id,
        "answer_text": "To detect a cycle in a linked list, we use Floyd's Cycle-Finding algorithm with two pointers: a slow pointer and a fast pointer moving at double speed. The time complexity is O(N) and space complexity is O(1). Um, basically it works well.",
        "duration_seconds": 18.5
    }
    status, body = make_request(f"{BASE_URL}/api/v1/interviews/sessions/turn", method="POST", data=turn_payload)
    print(f"[5/6] POST /api/v1/interviews/sessions/turn -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    turn_eval = body.get("turn_evaluation", {})
    assert "technical_score" in turn_eval, "Technical score missing"
    print(f"      Turn Tech Score: {turn_eval['technical_score']}/10, WPM: {turn_eval['wpm']}, Fillers: {turn_eval['filler_count']}")
    print(f"      Critique: {turn_eval['critique']}")

    # 6. GET /
    status, body = make_request(f"{BASE_URL}/")
    print(f"[6/6] GET / -> HTTP {status}")
    assert status == 200, f"Expected 200, got {status}"
    assert "CAMPUSPREP AI" in str(body), "Frontend title missing in index.html response"
    print("      Frontend index.html served successfully.")

    print("\nALL 6 ENDPOINT VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
