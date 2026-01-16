"""Define utilities for (mostly) auto-generating MCP tools.

This file will autogenerate a (Fast)MCP set of tools with
type annotations.

The resultant tools are perhaps too general for use in an MCP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mp_api.client import MPRester

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def get_annotation_signature(
    obj: Callable, tablen: int = 4
) -> tuple[str | None, str | None]:
    """Reconstruct the type annotations associated with a Callable.

    Returns the type annotations on input, and the output
    kwargs as str if type annotations can be inferred.
    """
    kwargs = None
    out_kwargs = None
    if (annos := obj.__annotations__) and (defaults := obj.__defaults__):
        non_ret_type = [k for k in annos if k != "return"]
        defaults = [f" = {val}" for val in defaults]
        if len(defaults) < len(non_ret_type):
            defaults = [""] * (len(non_ret_type) - len(defaults)) + defaults
        kwargs = ",\n".join(
            f"{' '*tablen}{k} : {v}{defaults[i]}"
            for i, (k, v) in enumerate(annos.items())
            if k != "return"
        )
        out_kwargs = ",\n".join(
            f"{' '*2*tablen}{k} = {k}" for k in annos if k != "return"
        )
    return kwargs, out_kwargs


def regenerate_tools(
    client: MPRester | None = None, file_name: str | Path | None = None
) -> str:
    """Utility to regenerate the informative tool names with annotations."""
    func_str = """# ruff: noqa
from __future__ import annotations

from datetime import datetime
from typing import Literal

from emmet.core.chemenv import (
    COORDINATION_GEOMETRIES,
    COORDINATION_GEOMETRIES_IUCR,
    COORDINATION_GEOMETRIES_IUPAC,
    COORDINATION_GEOMETRIES_NAMES,
)
from emmet.core.electronic_structure import BSPathType, DOSProjectionType
from emmet.core.grain_boundary import GBTypeEnum
from emmet.core.mpid import MPID
from emmet.core.thermo import ThermoType
from emmet.core.summary import HasProps
from emmet.core.symmetry import CrystalSystem
from emmet.core.synthesis import SynthesisTypeEnum, OperationTypeEnum
from emmet.core.vasp.calc_types import CalcType
from emmet.core.xas import Edge, Type

from pymatgen.analysis.magnetism.analyzer import Ordering
from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Structure
from pymatgen.electronic_structure.core import OrbitalType, Spin

"""

    translate = {
        "chemenv": "chemical_environment",
        "dos": "density_of_states",
        "eos": "equation_of_state",
        "summary": "material",
        "robocrys": "crystal_summary",
    }

    mp_client = client or MPRester()

    def _get_rester_sub_name(name, route) -> str | None:
        for y in [x for x in dir(route) if not x.startswith("_")]:
            attr = getattr(route, y)
            if (
                (hasattr(attr, "__name__") and attr.__name__ == name)
                or (hasattr(attr, "__class__"))
                and attr.__class__.__name__ == name
            ):
                return y
        return None

    for x in mp_client._all_resters:
        if not (
            sub_rest_route := _get_rester_sub_name(x.__name__, mp_client.materials)
        ):
            continue

        search_method = "search"
        if "robocrys" in x.__name__.lower():
            search_method = "search_docs"

        informed_name = sub_rest_route
        for k, v in translate.items():
            if k in informed_name:
                informed_name = informed_name.replace(k, v)

        kwargs, out_kwargs = get_annotation_signature(getattr(x, search_method))
        if not kwargs:
            # FastMCP raises a ValueError if types are not provided:
            # `Functions with **kwargs are not supported as tools`
            continue
        func_str += (
            f"def get_{informed_name}_data(\n"
            f"    self,\n{kwargs}\n) -> list[dict]:\n"
            f"    return self.client.materials.{sub_rest_route}"
            f".search(\n{out_kwargs}\n)\n\n"
        )

    helpers = [
        method
        for method in dir(mp_client)
        if any(
            method.startswith(signature)
            for signature in (
                "get",
                "find",
            )
        )
    ]
    for func_name in helpers:
        func = getattr(mp_client, func_name)
        # MCP doesn't work with LRU cached functions?
        if hasattr(func, "cache_info"):
            continue

        kwargs, out_kwargs = get_annotation_signature(func)
        if not kwargs:
            continue

        informed_name = func_name.replace("find", "get")
        for k, v in translate.items():
            if k in informed_name:
                informed_name = informed_name.replace(k, v)

        func_str += (
            f"def {informed_name}(\n"
            f"    self,\n{kwargs}\n) -> list[dict]:\n"
            f"    return self.client.{func_name}(\n"
            f"{out_kwargs}\n)\n\n"
        )

    if file_name:
        with open(file_name, "w") as f:
            f.write(func_str)

    return func_str
