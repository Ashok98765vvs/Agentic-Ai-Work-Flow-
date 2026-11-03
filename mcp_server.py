"""Independent MCP server exposing the same read-only demo data.
Connect from an MCP-capable client; the HTTP agent in app.py uses its own local tools.
"""
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('demo-project-tools')
TASKS = [
    {'id': 1, 'title': 'Review RAG eval set', 'status': 'open'},
    {'id': 2, 'title': 'Write API tests', 'status': 'done'},
    {'id': 3, 'title': 'Prepare deployment checklist', 'status': 'open'},
]
@mcp.tool()
def list_project_tasks(status: str = 'all') -> list[dict]:
    """Return fictional project tasks; filter by open, done, or all."""
    return [t for t in TASKS if status == 'all' or t['status'] == status]
@mcp.tool()
def utc_time() -> str:
    """Get current UTC time."""
    return datetime.now(timezone.utc).isoformat()
if __name__ == '__main__':
    mcp.run(transport='stdio')
