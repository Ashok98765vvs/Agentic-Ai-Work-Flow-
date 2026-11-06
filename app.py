"""Agentic AI Workflow Assistant using local Ollama."""

import logging
import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://host.docker.internal:11434/v1",
)
OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)

TASKS = [
    {
        "id": 1,
        "title": "Review RAG evaluation",
        "owner": "Demo Team",
        "status": "open",
    },
    {
        "id": 2,
        "title": "Write API tests",
        "owner": "Demo Team",
        "status": "done",
    },
    {
        "id": 3,
        "title": "Prepare deployment",
        "owner": "Demo Team",
        "status": "open",
    },
]


@tool
def list_tasks(status: str = "all") -> list[dict]:
    """List demo project tasks by status: all, open, done."""
    if status not in ("all", "open", "done"):
        return [{"error": "Invalid status"}]

    return [
        task for task in TASKS
        if status == "all" or task["status"] == status
    ]


@tool
def current_utc_time() -> str:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc).isoformat()


api = FastAPI(
    title="Agentic AI Workflow Assistant - Local Ollama",
    version="2.0.0",
)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)


@api.get("/")
def home():
    return {
        "message": "Local Agentic AI API is running",
        "provider": "ollama",
        "model": OLLAMA_MODEL,
    }


@api.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "local",
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "model_configured": True,
    }


@api.get("/tasks")
def get_tasks():
    return {
        "source": "fictional_demo_data",
        "tasks": TASKS,
    }


@api.post("/ask")
def ask(request: AskRequest):
    try:
        model = ChatOpenAI(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_URL,
            api_key="ollama",
            temperature=0,
            timeout=180,
            max_retries=0,
        )

        agent = create_agent(
            model=model,
            tools=[
                list_tasks,
                current_utc_time,
            ],
            system_prompt=(
                "You are a helpful local AI workflow assistant. "
                "For questions about project tasks, always call "
                "the list_tasks tool before answering. "
                "For current time questions, call current_utc_time. "
                "All tasks are fictional demo data. "
                "Do not claim access to real projects or MCP. "
                "You cannot modify tasks. "
                "Answer clearly and concisely."
            ),
        )

        messages = [
            {
                "role": turn.role,
                "content": turn.content,
            }
            for turn in request.history[-12:]
        ]

        messages.append({
            "role": "user",
            "content": request.question,
        })

        result = agent.invoke(
            {"messages": messages},
            config={"recursion_limit": 12},
        )

        content = result["messages"][-1].content

        if isinstance(content, str):
            answer = content
        elif isinstance(content, list):
            answer = "\n".join(
                str(part.get("text", ""))
                if isinstance(part, dict)
                else str(part)
                for part in content
            )
        else:
            answer = str(content)

        return {
            "answer": answer,
            "mode": "local",
            "provider": "ollama",
            "model": OLLAMA_MODEL,
        }

    except Exception as exc:
        logger.exception("Local Ollama agent failed")

        error_name = type(exc).__name__

        if "Connection" in error_name:
            detail = (
                "Cannot reach Ollama from Docker. "
                "Check Ollama and host.docker.internal."
            )
        elif "Timeout" in error_name:
            detail = (
                "Local model timed out. "
                "Check Mac memory and Ollama logs."
            )
        else:
            detail = (
                f"Local agent failed: {error_name}. "
                "Check Docker API logs."
            )

        raise HTTPException(
            status_code=502,
            detail=detail,
        ) from exc
