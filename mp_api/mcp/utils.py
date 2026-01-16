"""Define utilities for constructing MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mp_api.client import MPRester

if TYPE_CHECKING:
    from typing import Any

_REQUIRED_CLIENT_KWARGS = {
    "use_document_model": False,
    "include_user_agent": True,
}


class _NeedsMPClient:
    """Mix in to aid in API client interactions.

    Args:
        client_kwargs : dict of str, Any, or None
            Arguments to the API client.
            Note that `use_document_model` will always be set to `False`,
            and `include_user_agent` will always be set to True.

            Moreover, the user agent will start with `mp-mcp` rather than `mp-api`.
    """

    def __init__(
        self,
        client_kwargs: dict[str, Any] | None = None,
    ):
        self._client_kwargs = client_kwargs or {}
        self.reset_client()

    def __enter__(self):
        """Support for "with" context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for "with" context."""
        self.client.__exit__(exc_type, exc_val, exc_tb)

    def reset_client(self) -> None:
        """Reset the API client."""
        self.client = MPRester(
            **{
                **self._client_kwargs,
                **_REQUIRED_CLIENT_KWARGS,
            }
        )
        self.client.session.headers["user-agent"] = self.client.session.headers[
            "user-agent"
        ].replace("mp-api", "mp-mcp")

    def update_user_api_key(self, api_key: str) -> None:
        """Change the API key used in the client.

        Call this method to set the user's API correctly.
        Ask the user for their API key as plain text,
        and input the result to this method.
        """
        self._client_kwargs["api_key"] = api_key
        self.reset_client()
