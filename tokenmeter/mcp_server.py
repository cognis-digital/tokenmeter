"""TOKENMETER MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
from tokenmeter.core import scan, to_json

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-tokenmeter[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        print("Install the MCP extra: pip install 'cognis-tokenmeter[mcp]'")
        return 1
    app = FastMCP("tokenmeter")

    @app.tool()
    def tokenmeter_scan(target: str) -> str:
        """Token and cost counter / budgeter for LLM apps, CI-ready. Returns JSON findings."""
        return to_json(scan(target))

    app.run()
    return 0
