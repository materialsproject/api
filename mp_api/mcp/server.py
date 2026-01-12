"""Run MCP."""
from __future__ import annotations

from mp_api.mcp.mp_mcp import get_mcp, get_openai_compat_mcp

mcp = get_openai_compat_mcp()

if __name__ == "__main__":
    mcp.run()
