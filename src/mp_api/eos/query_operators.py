from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict


class EnergyVolumeQuery(QueryOperator):
    """
    Method to generate a query for ranges of equations of state energies and volumes
    """

    def query(
        self,
        volume_max: Optional[float] = Query(
            None, description="Maximum value for the cell volume in A³/atom.",
        ),
        volume_min: Optional[float] = Query(
            None, description="Minimum value for the cell volume in A³/atom.",
        ),
        energy_max: Optional[float] = Query(
            None, description="Maximum value for the energy in eV/atom.",
        ),
        energy_min: Optional[float] = Query(
            None, description="Minimum value for the energy in eV/atom.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "volume": [volume_min, volume_max],
            "energy": [energy_min, energy_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = ["volume", "energy"]
        return [(key, False) for key in keys]
