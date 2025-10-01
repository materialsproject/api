"""Define custom MCP tools for the Materials Project API."""
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field, PrivateAttr

from mp_api.client import MPRester
from mp_api.mcp import tools as mcp_tools


class MPMcp(BaseModel):
    name: str = Field("Materials_Project_MCP")
    client_kwargs: dict[str, Any] | None = Field(None)
    _client: MPRester | None = PrivateAttr(None)

    @property
    def client(self) -> MPRester:
        # Always return JSON compliant output for MCP
        if not self._client:
            kwargs = {
                **(self.client_kwargs or {}),
                "use_document_model": False,
                "monty_decode": False,
            }
            self._client = MPRester(**kwargs)
        return self._client

    def mcp(self, **kwargs) -> FastMCP:
        mcp = FastMCP(self.name, **kwargs)

        for attr in {x for x in dir(mcp_tools) if x.startswith("get")}:
            mcp.tool(getattr(mcp_tools, attr))

        return mcp

    def bootstrap_mcp(self, **kwargs) -> FastMCP:
        """Bootstrap an MP API MCP only from the OpenAPI spec."""
        return FastMCP.from_openapi(
            openapi_spec=httpx.get(
                urljoin(self.client.endpoint, "openapi.json")
            ).json(),
            client=httpx.AsyncClient(
                base_url=self.client.endpoint,
                headers={"x-api-key": self.client.api_key},
            ),
            name=self.name,
            **kwargs,
        )
