# Agentic AI Workflow Assistant — Docker + Streamlit

An executable **local demo**, adapted from the supplied `app.py` and `mcp_server.py`.

## What is real and what is a demo?

- **Working path (once started and configured):** Streamlit chat UI → FastAPI `POST /ask` → LangChain agent (LangGraph runtime) → OpenAI model → local Python tools → response.
- **Real clock:** `current_utc_time()` gets current UTC time.
- **Fictional data:** three in-memory project tasks. Task editing and persistence are **not implemented**.
- **Not connected:** supplied `mcp_server.py` runs separately as a stdio MCP prototype; the FastAPI agent does **not** invoke it.
- **Not production ready:** no authentication, persistent history, rate limits, cloud deployment, or external task access. Ports bind to localhost only.

## Prerequisites

- Mac with Docker Desktop running (or another machine with Docker Engine + Compose plugin)
- An OpenAI API key with usable API credits/access for the configured model

## Start

Open Terminal and `cd` into the folder containing `compose.yaml`.

```bash
cp .env.example .env
```

Edit `.env` and replace `replace_with_your_api_key` with a real OpenAI API key. **Do not share or commit `.env`.**

```bash
docker compose up --build -d
docker compose ps
```

Open:

- **Chat dashboard:** http://localhost:8501
- **Swagger API docs:** http://localhost:8000/docs
- **Health endpoint:** http://localhost:8000/health

Chat example: **What are my open project tasks?**

## Verify responses

```bash
curl http://localhost:8000/health
curl http://localhost:8000/tasks
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What are my open demo tasks?"}'
```

From your Mac (Python 3 installed):

```bash
python3 tests/smoke_test.py
TEST_LLM=1 python3 tests/smoke_test.py
```

`TEST_LLM=1` performs a paid external OpenAI API request; the default smoke test does not.

To inspect containers:

```bash
docker compose logs -f api dashboard
docker compose down
```

If ports 8000 or 8501 are in use, stop the other local service or change the host-side port in `compose.yaml`. You can run `docker compose down` from the previous stack before starting this one.

## Source tree

```text
.
├── app.py                     # FastAPI application and local demo tools
├── mcp_server.py              # Standalone prototype, NOT connected
├── Dockerfile                 # Backend image
├── requirements.txt
├── compose.yaml               # Backend + dashboard
├── .env.example
├── .dockerignore
├── dashboard/
│   ├── Dockerfile             # Streamlit image
│   ├── requirements.txt
│   └── main.py
├── tests/
│   └── smoke_test.py
└── assets/
    └── architecture.png      # Original architecture reference (not yet current)
```

## Limitations and next steps

This is a read-only starter app. Add `langchain-mcp-adapters` and a real MCP client before claiming MCP tools are used by the agent. Add SQLite/Postgres and write endpoints before claiming task updates or saved task state. For public/cloud deployment, add authentication, authorization, secret management, rate limiting, and proper observability.

Dependencies intentionally use bounded version ranges for compatibility with the original project. For reproducible releases, resolve and lock exact package versions after a successful build.
