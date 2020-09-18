from typing import Optional, Union
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.dos.models.core import (
    DOSProjection,
    SpinChannel,
    OrbitalType,
)
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
            SpinChannel.spin_up,
            description="Spin channel of dos to query on. +1 (-1) corresponds to spin-up (spin-down). \
                For non spin polarized calculation, \
                data will be in the +1 (spin-up) entry.",
        ),
        element: Optional[Element] = Query(
            None, description="Element to query on for elements projected data.",
        ),
        orbital: Optional[OrbitalType] = Query(
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

        d = {}

        energy_range = {
            str(spin_channel.value): {"$gte": energy_min, "$lte": energy_max}
        }

        crit = defaultdict(dict)

        if projection == "total":
            crit["dos"] = {str(projection.value): energy_range}
        elif projection == "orbital":
            crit["dos"] = {str(projection.value): {str(orbital.value): energy_range}}
        elif projection == "element":
            if orbital is not None:
                crit["dos"] = {
                    str(projection.value): {
                        str(element.value): {str(orbital.value): energy_range}
                    }
                }
            else:
                crit["dos"] = {
                    str(projection.value): {str(element.value): {"total": energy_range}}
                }

        return {"criteria": crit}

