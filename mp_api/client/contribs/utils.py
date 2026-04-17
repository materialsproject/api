"""Define utility functions for MPContribs client."""

from __future__ import annotations

import gzip
import sys
from hashlib import md5
from typing import TYPE_CHECKING

import orjson
from jsonschema.exceptions import ValidationError
from swagger_spec_validator.common import SwaggerValidationError

from mp_api.client.contribs.settings import MPCC_SETTINGS
from mp_api.client.core.exceptions import MPContribsClientError

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any

_ipython = getattr(sys.modules.get("IPython"), "get_ipython", lambda: None)()


def _in_ipython() -> bool:
    """Check if running in IPython/Jupyter."""
    return _ipython is not None and "IPKernelApp" in getattr(_ipython, "config", {})


if _in_ipython():

    def _hide_traceback(
        exc_tuple=None,
        filename=None,
        tb_offset=None,
        exception_only=False,
        running_compiled_code=False,
    ):
        etype, value, tb = sys.exc_info()

        if issubclass(
            etype, (MPContribsClientError, SwaggerValidationError, ValidationError)
        ):
            return _ipython._showtraceback(
                etype, value, _ipython.InteractiveTB.get_exception_only(etype, value)
            )

        return _ipython._showtraceback(
            etype, value, _ipython.InteractiveTB(etype, value, tb)
        )

    _ipython.showtraceback = _hide_traceback  # type: ignore[union-attr]


def _compress(data: Any) -> tuple[int, bytes]:
    """Write JSONable data to gzipped bytes.

    Args:
        data (Any) : JSONable python object

    Returns:
        int : the length of the compressed data
        bytes : the compressed data
    """
    content = gzip.compress(orjson.dumps(data))
    return len(content), content


def _chunk_by_size(
    items: Any, max_size: float = 0.95 * MPCC_SETTINGS.MAX_BYTES
) -> Generator:
    """Compress a large data structure by chunks.

    Args:
        items (Any) : JSONable python object(s)
        max_size (float) : The maximum size of an object in bytes
            to put into the buffer.

    Returns:
        bytes : the compressed data
    """
    buffer, buffer_size = [], 0

    for item in items:
        item_size = _compress(item)[0]

        if buffer_size + item_size <= max_size:
            buffer.append(item)
            buffer_size += item_size
        else:
            yield buffer
            buffer = [item]
            buffer_size = item_size

    if buffer_size > 0:
        yield buffer


def get_md5(d: dict[str, Any]) -> str:
    """Get the MD5 of a JSONable dict."""
    s = orjson.dumps({k: d[k] for k in sorted(d)})
    return md5(s).hexdigest()


def flatten_dict(dct: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Recursively flatten a dictionary.

    Args:
        dct (dict of str, Any) : dictionary to flatten
        separator (str = ".") : the separator to use to indicate nested keys

    Returns:
        dict of str, Any : the flattened dict
    """
    flattened: dict[str, Any] = {}

    def _flatten(obj: Any, key: str | None) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                _flatten(v, f"{key}{separator}{k}" if key else k)
        elif key is not None:
            flattened[key] = obj

    _flatten(dct, None)
    return flattened


def unflatten_dict(dct: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Recursively nest a flattened dictionary.

    Args:
        dct (dict of str, Any) : flattened dictionary
        separator (str = ".") : the separator to use to indicate nested keys

    Returns:
        dict of str, Any : the nested dict
    """
    unflattened: dict[str, Any] = {}

    def _set_value(key, value):
        for i, x in enumerate(split_key := key.split(separator)):
            y = unflattened if i == 0 else v  # noqa: F821
            if x not in y:
                y[x] = {} if i < len(split_key) - 1 else value
            v = y[x]  # noqa: F841

    _ = [
        _set_value(k, dct[k])
        for k in sorted(dct, key=lambda x: x.count(separator), reverse=True)
    ]
    return unflattened
