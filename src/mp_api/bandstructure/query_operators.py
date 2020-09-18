from typing import Optional, Union
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.bandstructure.models.core import (
    BSPathType,
    BSDataFields,
)
from pymatgen.core.periodic_table import Element

from collections import defaultdict


class BSDataQuery(QueryOperator):
    """
    Method to generate a query over band structure summary data.
    """

    def query(
        self,
        path_type: BSPathType = Query(
            ..., description="Band structure k-path convention type.",
        ),
        data_field: BSDataFields = Query(..., description="Data field to query on."),
        energy_max: float = Query(
            ..., description="Maximum value for the energy in eV."
        ),
        energy_min: float = Query(
            ..., description="Minimum value for the energy in eV."
        ),
        direct: Optional[bool] = Query(
            None, description="Whether a band gap is direct or not."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)

        crit["bandstructure"] = {
            str(path_type.value): {str(data_field.value): {"energy": {}}}
        }

        d = [energy_min, energy_max]

        if d[0]:
            crit["bandstructure"][str(path_type.value)][str(data_field.value)][
                "energy"
            ] = {"$gte": d[0]}

        if d[1]:
            crit["bandstructure"][str(path_type.value)][str(data_field.value)][
                "energy"
            ] = {"$lte": d[1]}

        if direct is not None:
            crit["bandstructure"][str(path_type.value)][str(data_field.value)][
                "direct"
            ] = direct

        return {"criteria": crit}

