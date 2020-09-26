from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.dos.models.core import DOSProjection, DOSDataFields, SpinChannel
from pymatgen.electronic_structure.core import OrbitalType
from pymatgen.core.periodic_table import Element

from collections import defaultdict


class DOSDataQuery(QueryOperator):
    """
    Method to generate a query over density of states summary data.
    """

    def query(
        self,
        projection: DOSProjection = Query(
            ..., description="Projection data type for density of states.",
        ),
        spin_channel: SpinChannel = Query(
            ...,
            description="Spin channel of dos to query on. +1 (-1) corresponds to spin-up (spin-down). \
                For non spin polarized calculation, \
                data will be in the +1 (spin-up) entry.",
        ),
        data_field: DOSDataFields = Query(..., description="Data field to query on.",),
        element: Element = Query(
            None, description="Element to query on for elements projected data.",
        ),
        orbital: OrbitalType = Query(
            None,
            description="Orbital to query on for elements or orbital projected data.",
        ),
        energy_max: float = Query(
            ..., description="Maximum value for the energy in eV."
        ),
        energy_min: float = Query(
            ..., description="Minimum value for the energy in eV."
        ),
    ) -> STORE_PARAMS:

        energy_range = {"$gte": energy_min, "$lte": energy_max}

        crit = defaultdict(dict)  # type: dict

        if projection.value == "total":
            crit[
                f"total.{str(data_field.value)}.{str(spin_channel.value)}"
            ] = energy_range
        elif projection.value == "orbital":
            crit[
                f"orbital.{str(orbital.name)}.{str(data_field.value)}.{str(spin_channel.value)}"
            ] = energy_range
        elif projection == "element":
            if orbital is not None:
                crit[
                    f"element.{str(element.value)}. \
                        {str(orbital.name)}.{str(data_field.value)}.{str(spin_channel.value)}"
                ] = energy_range

            else:
                crit[
                    f"element.{str(element.value)}.total.{str(data_field.value)}.{str(spin_channel.value)}"
                ] = energy_range

        return {"criteria": crit}
