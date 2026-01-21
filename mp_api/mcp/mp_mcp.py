"""Define custom MCP tools for the Materials Project API."""
from __future__ import annotations

from fastmcp import FastMCP

from mp_api.mcp.tools import MPCoreMCP

MCP_SERVER_INSTRUCTIONS = """
This MCP server defines search and document retrieval capabilities
for data in the Materials Project.
Use the search tool to find relevant documents based on materials
keywords.
Then use the fetch tool to retrieve complete materials summary information.
"""


def get_core_mcp() -> FastMCP:
    """Create an MCP compatible with OpenAI models."""
    mp_mcp = FastMCP(
        "Materials_Project_MCP",
        instructions=MCP_SERVER_INSTRUCTIONS,
    )
    core_tools = MPCoreMCP()
    for k in {"search", "fetch"}:
        mp_mcp.tool(getattr(core_tools, k), name=k)
    return mp_mcp
