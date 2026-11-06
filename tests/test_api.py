import json
import os
from urllib.request import Request, urlopen

BASE = os.getenv("TEST_API_URL", "http://127.0.0.1:8000")


def api_get(path):
    with urlopen(f"{BASE}{path}", timeout=10) as response:
        return response.status, json.load(response)


def test_health_endpoint():
    status, data = api_get("/health")
    assert status == 200
    assert data["status"] == "ok"


def test_model_configuration():
    _, data = api_get("/health")
    assert data["model_configured"] is True
    assert data["provider"] == "ollama"
    assert data["model"] == "qwen2.5:3b"


def test_tasks_endpoint():
    status, data = api_get("/tasks")
    assert status == 200
    assert data["source"] == "fictional_demo_data"
    assert isinstance(data["tasks"], list)


def test_task_count():
    _, data = api_get("/tasks")
    assert len(data["tasks"]) == 3


def test_open_tasks():
    _, data = api_get("/tasks")
    open_tasks = [
        task for task in data["tasks"]
        if task["status"] == "open"
    ]
    assert len(open_tasks) == 2


def test_completed_tasks():
    _, data = api_get("/tasks")
    completed = [
        task for task in data["tasks"]
        if task["status"] == "done"
    ]
    assert len(completed) == 1


def test_ask_endpoint():
    payload = json.dumps({
        "question": "What are my open project tasks?"
    }).encode("utf-8")

    request = Request(
        f"{BASE}/ask",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        data = json.load(response)
        assert response.status == 200

    assert isinstance(data["answer"], str)
    assert data["answer"].strip()
    assert data["provider"] == "ollama"
