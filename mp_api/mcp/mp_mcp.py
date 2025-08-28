"""Define custom MCP tools for the Materials Project API."""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field, PrivateAttr

from mp_api.client import MPRester
from mp_api.mcp import tools as mcp_tools


class MPMcp(BaseModel):
    name: str = Field("Materials Project MCP")
    client_kwargs: dict[str, Any] | None = Field(None)
    _client: MPRester | None = PrivateAttr(None)

    @property
    def client(self) -> MPRester:
        # Always return JSON compliant output for MCP
        kwargs = {
            **(self.client_kwargs or {}),
            "use_document_model": False,
            "monty_decode": False,
        }
        if not self._client:
            self._client = MPRester(**kwargs)
        return self._client

    def mcp(self, **kwargs) -> FastMCP:
        mcp = FastMCP(self.name, **kwargs)

        for attr in {x for x in dir(mcp_tools) if x.startswith("get")}:
            mcp.tool(getattr(mcp_tools, attr))

        return mcp
