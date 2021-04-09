from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict


class PiezoelectricQuery(QueryOperator):
    """
    Method to generate a query for ranges of piezoelectric data
    """

    def query(
        self,
        piezo_modulus_max: Optional[float] = Query(
            None, description="Maximum value for the piezoelectric modulus in C/m².",
        ),
        piezo_modulus_min: Optional[float] = Query(
            None, description="Minimum value for the piezoelectric modulus in C/m².",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "piezo.e_ij_max": [piezo_modulus_min, piezo_modulus_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("piezo.e_ij_max", False)]
