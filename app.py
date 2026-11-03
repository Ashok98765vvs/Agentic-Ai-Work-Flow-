"""Agentic personal workflow demo. Tools use DEMO tasks only; no external actions."""
import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

TASKS = [
    {"id": 1, "title": "Review RAG eval set", "owner": "Ashok", "status": "open"},
    {"id": 2, "title": "Write API tests", "owner": "Ashok", "status": "done"},
    {"id": 3, "title": "Prepare deployment checklist", "owner": "Team", "status": "open"},
]

@tool
def list_tasks(status: str = "all") -> list[dict]:
    """List demo project tasks; status can be 'all', 'open', or 'done'."""
    if status not in ("all", "open", "done"):
        return []
    return [t for t in TASKS if status == "all" or t["status"] == status]

@tool
def current_utc_time() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()

api = FastAPI(title="Agentic AI Workflow Demo", version="0.1.0")
class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

@api.get('/health')
def health():
    return {"status": "ok", "mode": "demo"}

@api.post('/ask')
def ask(payload: Ask):
    if not os.getenv('OPENAI_API_KEY'):
        raise HTTPException(503, 'Set OPENAI_API_KEY before using the agent')
    agent = create_agent(
        model=ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'), temperature=0),
        tools=[list_tasks, current_utc_time],
        system_prompt=("You are a task assistant. Use tools for task status and current UTC time. "
                       "Tasks are fictional demo data. Never claim you changed a task or sent anything."),
    )
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": payload.question}]}, config={"recursion_limit": 12})
        output = result['messages'][-1].content
        return {"answer": str(output)}
    except Exception as exc:
        raise HTTPException(502, f'Agent request failed: {type(exc).__name__}') from exc
