"""Run MCP."""
from __future__ import annotations

from mp_api.mcp.mp_mcp import MPMcp

mcp = MPMcp().mcp()

if __name__ == "__main__":
    mcp.run()
