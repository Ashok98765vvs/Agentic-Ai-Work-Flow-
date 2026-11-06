"""Run after Docker Compose is up: python3 tests/smoke_test.py."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.getenv("TEST_API_URL", "http://127.0.0.1:8000")


def get(path):
    with urlopen(f"{BASE}{path}", timeout=8) as response:
        return json.load(response)


def run():
    health = get("/health")
    assert health["status"] == "ok", health
    print("PASS /health: backend online")
    tasks = get("/tasks")
    assert tasks["source"] == "fictional_demo_data" and len(tasks["tasks"]) == 3, tasks
    print("PASS /tasks: three fictional demo tasks returned")
    payload = json.dumps({"question": "List my open demo tasks"}).encode()
    req = Request(f"{BASE}/ask", data=payload, headers={"Content-Type": "application/json"})
    if not health.get("model_configured"):
        try:
            urlopen(req, timeout=15)
        except HTTPError as exc:
            assert exc.code == 503, exc.code
            print("PASS /ask: explicit 503 when API key missing (expected)")
        else:
            raise AssertionError("Expected /ask to reject missing key")
    elif os.getenv("TEST_LLM", "0") == "1":
        with urlopen(req, timeout=120) as response:
            answer = json.load(response)["answer"]
            assert answer.strip(), "Empty model answer"
            print("PASS /ask: live model call returned an answer:", answer[:300])
    else:
        print("SKIP /ask live model call: set TEST_LLM=1 to test (API usage charges may apply)")


if __name__ == "__main__":
    try:
        run()
    except (AssertionError, HTTPError, URLError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
