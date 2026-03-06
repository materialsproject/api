"""Define flask-dependent utilities for the web server."""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from flask import has_request_context as _has_request_context
    from flask import request
except ImportError:
    _has_request_context = None  # type: ignore[assignment]
    request = None  # type: ignore[assignment]

from mp_api.client.core.utils import validate_api_key

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


def has_request_context() -> bool:
    """Determine if the current context is a request.

    Returns:
    --------
    bool : True if in a request context
        False if flask is not installed or not in a request context.
    """
    return _has_request_context is not None and _has_request_context()


def get_request_headers() -> dict[str, Any]:
    """Get the headers if operating in a request context.

    Returns:
    --------
    dict of str to Any
        Empty dict if flask is not installed, or not in a request context.
        Request headers otherwise.
    """
    return request.headers if has_request_context() else {}


def is_dev_env(
    localhosts: Sequence[str] = ("localhost:", "127.0.0.1:", "0.0.0.0:")
) -> bool:
    """Determine if current env is local/developmental or production.

    Args:
        localhosts (Sequence of str) : A set of host prefixes for checking
            if the current environment is locally deployed.

    Returns:
        bool: True if the environment is locally hosted.
    """
    return (
        True
        if not has_request_context()
        else get_request_headers().get("Host", "").startswith(localhosts)
    )


def get_consumer() -> dict[str, str]:
    """Identify the consumer associated with the current request.

    Returns:
        dict of str to str, the headers associated with the consumer
    """
    if not has_request_context():
        return {}

    names = [
        "X-Consumer-Id",  # kong internal uuid
        "X-Consumer-Custom-Id",  # api key
        "X-Consumer-Username",  # <provider>:<email>
        "X-Anonymous-Consumer",  # is anonymous user?
        "X-Authenticated-Groups",  # groups this user belongs to
        "X-Consumer-Groups",  # same as X-Authenticated-Groups
    ]
    headers = get_request_headers()
    return {name: headers[name] for name in names if headers.get(name) is not None}


def is_logged_in_user(consumer: dict[str, str] | None = None) -> bool:
    """Check if the client has the necessary headers for an authenticated user.

    Args:
        consumer (dict of str to str, or None): Headers associated with the consumer

    Returns:
        bool : True if the consumer is a logged-in user, False otherwise.
    """
    c = consumer or get_consumer()
    return bool(not c.get("X-Anonymous-Consumer") and c.get("X-Consumer-Id"))


def get_user_api_key(
    api_key: str | None = None, consumer: dict[str, str] | None = None
) -> str | None:
    """Get the api key that belongs to the current user.

    If running on localhost, api key is obtained from
    the environment variable MP_API_KEY.

    Args:
        api_key (str or None) : User API key
        consumer (dict of str to str, or None): Headers associated with the consumer

    Returns:
        str, the API key, or None if no API key could be identified.
    """
    if is_dev_env():
        return validate_api_key(api_key=api_key)
    elif is_logged_in_user(c := consumer or get_consumer()):
        return c.get("X-Consumer-Custom-Id")
    return None
