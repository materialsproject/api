"""Run MCP."""
from __future__ import annotations

from mp_api.mcp.mp_mcp import MPMcp

MP_MCP = MPMcp().mcp()
MP_MCP.run()
