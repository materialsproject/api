from typing import Optional, Union
from fastapi import Query, HTTPException
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

        if data_field.value == "band_gap" and direct is None:
            raise HTTPException(
                status_code=404, detail="Must specify whether the band gap is direct.",
            )

        d = [energy_min, energy_max]

        crit[f"{str(path_type.name)}.{str(data_field.value)}.energy"]["$gte"] = d[0]

        crit[f"{str(path_type.name)}.{str(data_field.value)}.energy"]["$lte"] = d[1]

        if direct is not None:
            crit[f"{str(path_type.name)}.{str(data_field.value)}.direct"] = direct

        return {"criteria": crit}

