from __future__ import annotations

import os
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


def validate_api_key(api_key: str | None = None) -> str:
    """Find and validate an API key."""
    # SETTINGS tries to read API key from ~/.config/.pmgrc.yaml
    api_key = api_key or os.getenv("MP_API_KEY")
    if not api_key:
        from pymatgen.core import SETTINGS

        api_key = SETTINGS.get("PMG_MAPI_KEY")

    if not api_key or len(api_key) != 32:
        addendum = " Valid API keys are 32 characters." if api_key else ""
        raise ValueError(
            "Please obtain a valid API key from https://materialsproject.org/api "
            f"and export it as an environment variable `MP_API_KEY`.{addendum}"
        )

    return api_key


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
