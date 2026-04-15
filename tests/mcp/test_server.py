import asyncio
import pytest

try:
    import fastmcp
except ImportError:
    pytest.skip(
        "Please `pip install fastmcp` to test the MCP server directly.",
        allow_module_level=True,
    )

from mp_api.client.core.exceptions import MPRestError
from mp_api.mcp.server import get_core_mcp, parse_server_args, MCP_SERVER_INSTRUCTIONS


async def get_mcp_tools():
    core_mcp = get_core_mcp()
    if hasattr(core_mcp, "get_tools"):  # fastmcp < 3
        return set(await core_mcp.get_tools())
    # fastmcp >= 3
    return {tool.name for tool in await core_mcp.list_tools()}


async def get_mcp_tool(tool_name):
    return await get_core_mcp().get_tool(tool_name)


def test_mcp_server():
    assert asyncio.run(get_mcp_tools()) == {
        "fetch",
        "fetch_many",
        "fetch_all",
        "search",
        "get_phase_diagram_from_elements",
    }

    search_tool = asyncio.run(get_mcp_tool("search"))
    assert search_tool.parameters["properties"] == {"query": {"type": "string"}}
    fetch_tool = asyncio.run(get_mcp_tool("fetch"))
    assert fetch_tool.parameters["properties"] == {"idx": {"type": "string"}}

    mcp_server = get_core_mcp()
    assert isinstance(mcp_server, fastmcp.FastMCP)
    assert mcp_server.instructions == MCP_SERVER_INSTRUCTIONS


def test_server_cli():
    assert parse_server_args(
        ["--port", "-500", "--host", "0.0.0", "--transport", "sse"]
    ) == {"port": -500, "host": "0.0.0", "transport": "sse"}

    with pytest.raises(MPRestError, match="Invalid `transport="):
        _ = parse_server_args(["--transport", "magic"])
