"""Run MCP."""
from __future__ import annotations

from mp_api.mcp.mp_mcp import get_mcp

mcp = get_mcp()

if __name__ == "__main__":
    mcp.run()
