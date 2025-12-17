from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Literal

import orjson
from emmet.core import __version__ as _EMMET_CORE_VER
from emmet.core.mpid_ext import validate_identifier
from monty.json import MontyDecoder
from packaging.version import parse as parse_version

from mp_api.client.core.settings import MAPIClientSettings

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


def validate_ids(id_list: list[str]) -> list[str]:
    """Function to validate material and task IDs.

    Args:
        id_list (List[str]): List of material or task IDs.

    Raises:
        ValueError: If at least one ID is not formatted correctly.

    Returns:
        id_list: Returns original ID list if everything is formatted correctly.
    """
    if len(id_list) > MAPIClientSettings().MAX_LIST_LENGTH:
        raise ValueError(
            "List of material/molecule IDs provided is too long. Consider removing the ID filter to automatically pull"
            " data for all IDs and filter locally."
        )

    # TODO: after the transition to AlphaID in the document models,
    # The following line should be changed to
    # return [validate_identifier(idx,serialize=True) for idx in id_list]
    return [str(validate_identifier(idx)) for idx in id_list]

class LazyImport:

    __slots__ = ["_module_name", "_class_name", "_obj"]

    def __init__(self, module_name : str, class_name : str,) -> None:
        self._module_name = module_name
        self._class_name = class_name
        self._obj = None
    
    def __str__(self) -> str:
        return f"LazyImport of {self._module_name}.{self._class_name}"
    
    def __repr__(self) -> str:
        return self.__str__()

    def __call__(self, *args, **kwargs):
        if self._obj is None:
            try:
                self._obj = getattr(
                    import_module(self._module_name),
                    self._class_name
                )(
                    *args,
                    **kwargs,
                )
            except Exception as exc:
                raise ImportError(
                    f"Failed to import {self._class_name}:\n{exc}"
                )
        return self._obj
    
    def __getattr__(self,v):
        return getattr(self._obj,v)
