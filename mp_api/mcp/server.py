"""Configure the Materials Project MCP server."""
from __future__ import annotations

from argparse import ArgumentParser
from typing import TYPE_CHECKING, get_args

from fastmcp import FastMCP
from fastmcp.server.server import Transport

from mp_api.client.core.exceptions import MPRestError
from mp_api.mcp.tools import MPCoreMCP

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

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


def parse_server_args(args: Sequence[str] | None = None) -> dict[str, Any]:
    """Parse CLI arguments for server configuration."""
    server_config = {"transport", "host", "port"}
    transport_vals = get_args(Transport)

    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "--transport",
        type=str,
        required=False,
    )
    arg_parser.add_argument(
        "--host",
        type=str,
        required=False,
    )
    arg_parser.add_argument(
        "--port",
        type=int,
        required=False,
    )

    parsed_args = arg_parser.parse_args(args=args)
    kwargs = {}
    for k in server_config:
        if (v := getattr(parsed_args, k, None)) is not None:
            if k == "transport" and v not in transport_vals:
                raise MPRestError(
                    f"Invalid `transport={v}`, choose one of: {', '.join(transport_vals)}"
                )
            kwargs[k] = v
    return kwargs


mcp = get_core_mcp()

if __name__ == "__main__":
    mcp.run(**parse_server_args())
