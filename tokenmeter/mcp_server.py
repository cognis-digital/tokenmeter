"""TOKENMETER MCP server — exposes estimate() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
import json
import sys

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
        pip install "cognis-tokenmeter[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "error: MCP extra not installed. Run: pip install 'cognis-tokenmeter[mcp]'",
            file=sys.stderr,
        )
        return 1
    from tokenmeter.core import estimate

    app = FastMCP("tokenmeter")

    @app.tool()
    def tokenmeter_estimate(
        text: str,
        model: str = "claude-sonnet",
        output_tokens: int = 0,
    ) -> str:
        """Estimate token count and cost for the given text. Returns JSON."""
        try:
            est = estimate(text, model=model, output_tokens=output_tokens)
        except (KeyError, ValueError) as exc:
            return json.dumps({"error": str(exc)})
        return json.dumps(est.to_dict())

    app.run()
    return 0
