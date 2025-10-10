"""Define custom MCP tools for the Materials Project API."""
from __future__ import annotations

from urllib.parse import urljoin

import httpx
from fastmcp import FastMCP

from mp_api.mcp.tools import MPMcpTools
from mp_api.mcp.utils import _NeedsMPClient


def get_mcp() -> FastMCP:
    """MCP with finer depth of control over tool names."""
    mp_mcp = FastMCP("Materials_Project_MCP")
    mcp_tools = MPMcpTools()
    for attr in {x for x in dir(mcp_tools) if x.startswith("get_")}:
        mp_mcp.tool(getattr(mcp_tools, attr))
    return mp_mcp


def get_bootstrap_mcp() -> FastMCP:
    """Bootstrap an MP API MCP only from the OpenAPI spec."""
    client = _NeedsMPClient().client

    return FastMCP.from_openapi(
        openapi_spec=httpx.get(urljoin(client.endpoint, "openapi.json")).json(),
        client=httpx.AsyncClient(
            base_url=client.endpoint,
            headers={"x-api-key": client.api_key},
        ),
        name="MP_OpenAPI_MCP",
    )
