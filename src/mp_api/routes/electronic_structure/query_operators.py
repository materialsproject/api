from sys import version_info
from typing import Optional, Union
from fastapi import Query, HTTPException
from pymatgen.analysis.magnetism.analyzer import Ordering
from pymatgen.electronic_structure.core import Spin, OrbitalType
from pymatgen.core.periodic_table import Element
from emmet.core.mpid import MPID

from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from mp_api.routes.electronic_structure.models.core import BSPathType, DOSProjectionType

from collections import defaultdict

if version_info >= (3, 8):
    from typing import Literal  # type: ignore
else:
    from typing_extensions import Literal


class ESSummaryDataQuery(QueryOperator):
    """
    Method to generate a query on electronic structure summary data.
    """

    def query(
        self,
        magnetic_ordering: Optional[Ordering] = Query(
            None, description="Magnetic ordering associated with the data."
        ),
        is_gap_direct: Optional[bool] = Query(
            None, description="Whether a band gap is direct or not."
        ),
        is_metal: Optional[bool] = Query(
            None, description="Whether the material is considered a metal."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if magnetic_ordering:
            crit["magnetic_ordering"] = magnetic_ordering.value

        if is_gap_direct is not None:
            crit["is_gap_direct"] = is_gap_direct

        if is_metal is not None:
            crit["is_metal"] = is_metal

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover

        keys = ["band_gap", "efermi", "magnetic_ordering", "is_gap_direct", "is_metal"]

        return [(key, False) for key in keys]


class BSDataQuery(QueryOperator):
    """
    Method to generate a query on band structure data.
    """

    def query(
        self,
        path_type: Optional[BSPathType] = Query(
            None, description="k-path selection convention for the band structure.",
        ),
        band_gap_max: Optional[float] = Query(
            None, description="Maximum value for the band gap energy in eV."
        ),
        band_gap_min: Optional[float] = Query(
            None, description="Minimum value for the band gap energy in eV."
        ),
        efermi_max: Optional[float] = Query(
            None, description="Maximum value for the fermi energy in eV."
        ),
        efermi_min: Optional[float] = Query(
            None, description="Minimum value for the fermi energy in eV."
        ),
        magnetic_ordering: Optional[Ordering] = Query(
            None, description="Magnetic ordering associated with the data."
        ),
        is_gap_direct: Optional[bool] = Query(
            None, description="Whether a band gap is direct or not."
        ),
        is_metal: Optional[bool] = Query(
            None, description="Whether the material is considered a metal."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if path_type is not None:

            d = {
                f"bandstructure.{path_type.value}.band_gap": [
                    band_gap_min,
                    band_gap_max,
                ],
                f"bandstructure.{path_type.value}.efermi": [efermi_min, efermi_max],
            }

            for entry in d:
                if d[entry][0] is not None:
                    crit[entry]["$gte"] = d[entry][0]

                if d[entry][1] is not None:
                    crit[entry]["$lte"] = d[entry][1]

            if magnetic_ordering:
                crit[
                    f"bandstructure.{path_type.value}.magnetic_ordering"
                ] = magnetic_ordering.value

            if is_gap_direct is not None:
                crit[f"bandstructure.{path_type.value}.is_gap_direct"] = is_gap_direct

            if is_metal is not None:
                crit[f"bandstructure.{path_type.value}.is_metal"] = is_metal

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover

        keys = ["bandstructure"]

        for bs_type in BSPathType:
            for field in ["band_gap", "efermi"]:
                keys.append(f"bandstructure.{bs_type.value}.{field}")

        return [(key, False) for key in keys]


class DOSDataQuery(QueryOperator):
    """
    Method to generate a query on density of states summary data.
    """

    def query(
        self,
        projection_type: Optional[DOSProjectionType] = Query(
            None, description="Projection type for the density of states data.",
        ),
        spin: Optional[Union[Literal["1", "-1"], Spin]] = Query(
            None,
            description="Spin channel for density of states data. '1' corresponds to spin up.",
        ),
        element: Optional[Element] = Query(
            None, description="Element type for projected density of states data.",
        ),
        orbital: Optional[OrbitalType] = Query(
            None, description="Orbital type for projected density of states data.",
        ),
        band_gap_max: Optional[float] = Query(
            None, description="Maximum value for the band gap energy in eV."
        ),
        band_gap_min: Optional[float] = Query(
            None, description="Minimum value for the band gap energy in eV."
        ),
        efermi_max: Optional[float] = Query(
            None, description="Maximum value for the fermi energy in eV."
        ),
        efermi_min: Optional[float] = Query(
            None, description="Minimum value for the fermi energy in eV."
        ),
        magnetic_ordering: Optional[Ordering] = Query(
            None, description="Magnetic ordering associated with the data."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if isinstance(spin, str):
            spin = Spin(int(spin))

        if projection_type is not None:
            if spin is None:
                raise HTTPException(
                    status_code=400,
                    detail="Must specify a spin channel for querying dos summary data.",
                )
            else:

                d = {
                    "band_gap": [band_gap_min, band_gap_max],
                    "efermi": [efermi_min, efermi_max],
                }

                for entry in d:
                    if projection_type.value == "total":

                        key_prefix = f"total.{str(spin.value)}"

                    elif projection_type.value == "orbital":

                        if orbital is None:
                            raise HTTPException(
                                status_code=400,
                                detail="Must specify an orbital type for querying orbital projection data.",
                            )

                        key_prefix = f"orbital.{str(orbital.name)}.{str(spin.value)}"

                    elif projection_type.value == "elemental":

                        if element is None:
                            raise HTTPException(
                                status_code=400,
                                detail="Must specify an element type for querying element projection data.",
                            )

                        if orbital is not None:
                            key_prefix = f"elemental.{str(element.value)}.{str(orbital.name)}.{str(spin.value)}"

                        else:
                            key_prefix = f"elemental.{str(element.value)}.total.{str(spin.value)}"

                    key = f"dos.{key_prefix}.{entry}"

                    if d[entry][0] is not None:
                        crit[key]["$gte"] = d[entry][0]
                    if d[entry][1] is not None:
                        crit[key]["$lte"] = d[entry][1]

        if magnetic_ordering:
            crit.update({"dos.magnetic_ordering": magnetic_ordering.value})

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover

        keys = ["dos", "dos.magnetic_ordering"]

        for proj_type in DOSProjectionType:
            keys.append(f"dos.{proj_type.value}.$**")

        return [(key, False) for key in keys]


class ObjectQuery(QueryOperator):
    """
    Method to generate a query on electronic structure object data.
    """

    def query(
        self,
        task_id: MPID = Query(
            ...,
            description="The calculation (task) ID associated with the data object",
        ),
    ) -> STORE_PARAMS:

        return {"criteria": {"task_id": str(task_id)}}
