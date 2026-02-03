from __future__ import annotations

import os
import warnings
from importlib import import_module
from typing import TYPE_CHECKING, Literal
from urllib.parse import urljoin

import orjson
from emmet.core import __version__ as _EMMET_CORE_VER
from emmet.core.mpid_ext import validate_identifier
from monty.json import MontyDecoder
from packaging.version import parse as parse_version

from mp_api.client.core.exceptions import MPRestError, MPRestWarning
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

if TYPE_CHECKING:
    from typing import Any


def _compare_emmet_ver(
    ref_version: str, op: Literal["==", ">", ">=", "<", "<="]
) -> bool:
    """Compare the current emmet-core version to a reference for version guarding.

    Example:
        _compare_emmet_ver("0.84.0rc0","<") returns
        emmet.core.__version__ < "0.84.0rc0"

    This function may not be used anywhere in the client, but it should
    be preserved for future use, in case some degree of backwards
    compatibility or feature buy-in is needed.

    Parameters
    -----------
    ref_version : str
        A reference version of emmet-core
    op : A mathematical operator
    """
    op_to_op = {"==": "eq", ">": "gt", ">=": "ge", "<": "lt", "<=": "le"}
    return getattr(
        parse_version(_EMMET_CORE_VER),
        f"__{op_to_op.get(op,op)}__",
    )(parse_version(ref_version))


def load_json(
    json_like: str | bytes, deser: bool = False, encoding: str = "utf-8"
) -> Any:
    """Utility to load json in consistent manner."""
    data = orjson.loads(
        json_like if isinstance(json_like, bytes) else json_like.encode(encoding)
    )
    return MontyDecoder().process_decoded(data) if deser else data


def validate_api_key(api_key: str | None = None) -> str | None:
    """Find and validate an API key."""
    # SETTINGS tries to read API key from ~/.config/.pmgrc.yaml
    api_key = api_key or os.getenv("MP_API_KEY")
    if not api_key:
        from pymatgen.core import SETTINGS as PMG_SETTINGS

        api_key = PMG_SETTINGS.get("PMG_MAPI_KEY")

    if not api_key:
        # The web server requires the client to initialize without an API key.
        # Only warn the user if the API key cannot be identified to permit
        # the web server to run.
        warnings.warn(
            "No API key found, please set explicitly or in "
            "the `MP_API_KEY` environment variable.",
            category=MPRestWarning,
            stacklevel=2,
        )

    elif isinstance(api_key, str) and len(api_key) != 32:
        raise MPRestError(
            "Please obtain a valid API key from https://materialsproject.org/api "
            "and export it as an environment variable `MP_API_KEY`. "
            "Valid API keys are 32 characters."
        )

    return api_key


def validate_ids(id_list: list[str]) -> list[str]:
    """Function to validate material and task IDs.

    Args:
        id_list (List[str]): List of material or task IDs.

    Raises:
        MPRestError: If at least one ID is not formatted correctly.

    Returns:
        id_list: Returns original ID list if everything is formatted correctly.
    """
    if len(id_list) > MAPI_CLIENT_SETTINGS.MAX_LIST_LENGTH:
        raise MPRestError(
            "List of material/molecule IDs provided is too long. Consider removing the ID filter to automatically pull"
            " data for all IDs and filter locally."
        )

    # TODO: after the transition to AlphaID in the document models,
    # The following line should be changed to
    # return [validate_identifier(idx,serialize=True) for idx in id_list]
    return [str(validate_identifier(idx)) for idx in id_list]


def validate_endpoint(endpoint: str | None, suffix: str | None = None) -> str:
    """Validate an endpoint with optional suffix.

    NB: does not modify the endpoint in place,
    returns a new variable.

    Parameters
    -----------
    endpoint : str or None (default)
        A string representing the endpoint URL or the default
        in `mp_api.client.core.settings`
    suffix : str or None (default)
        Optional suffix to append to the endpoint.

    Returns:
    -----------
    str : the validated endpoint
    """
    new_endpoint = endpoint or MAPI_CLIENT_SETTINGS.ENDPOINT
    if suffix:
        new_endpoint = urljoin(new_endpoint, suffix)
    if not new_endpoint.endswith("/"):
        new_endpoint += "/"
    return new_endpoint


class LazyImport:
    """Lazily import and load an object.

    This class is super lazy, in that it lazily imports and caches an object.
    If the object is a function, the function itself will be cached.

    If the object is a class, and the class is initialized, the
    current instance of the class will be cached.

    Parameters
    -----------
    import_str : str
        A dot-separated, import-like string.
    """

    __slots__ = ["_module_name", "_class_name", "_obj", "_imported"]

    def __init__(
        self,
        import_str: str,
    ) -> None:
        """Initialize a lazily imported object.

        Parameters
        -----------
        import_str : str
            A dot-separated, import-like string.
        """
        if len(split_import_str := import_str.rsplit(".", 1)) > 1:
            self._module_name, self._class_name = split_import_str
        else:
            self._module_name = split_import_str[0]
            self._class_name = None

        self._imported: Any | None = None
        self._obj: Any | None = None

    def copy(self) -> LazyImport:
        """Return a new copy of the current instance."""
        return LazyImport(
            f"{self._module_name}"
            + (f".{self._class_name}" if self._class_name else "")
        )

    def __str__(self) -> str:
        return f"LazyImport of {self._module_name}" + (
            f".{self._class_name}" if self._class_name else ""
        )

    def __repr__(self) -> str:
        return self.__str__()

    def _load(
        self,
    ) -> None:
        try:
            _imported = import_module(self._module_name)
            if self._class_name:
                _imported = getattr(_imported, self._class_name)
            self._imported = _imported
        except Exception as exc:
            raise ImportError(
                f"Failed to import {self._module_name}.{self._class_name}:\n{exc}"
            )

    def __call__(self, *args, **kwargs) -> Any:
        """Call a function or (re-)initialize a class.

        If the object itself has not been imported, this will first import it.

        If the object is a class, it will be initialized, cached, and returned.

        If the object is a function, it will be cached, and this will return
        the value(s) of the function at (*args,**kwargs).
        """
        if self._imported is None:
            self._load()

        if isinstance(self._imported, type):
            self._obj = self._imported(*args, **kwargs)
            return self._obj
        else:
            self._obj = self._imported
            return self._obj(*args, **kwargs)

    def __getattr__(self, v: str) -> Any:
        """Get an attribute on a super lazy object."""
        if self._obj is not None and hasattr(self._obj, v):
            return getattr(self._obj, v)

        if self._imported is None:
            self._load()
        if hasattr(self._imported, v):
            return getattr(self._imported, v)
