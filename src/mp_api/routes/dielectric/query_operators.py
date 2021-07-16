from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict


class DielectricQuery(QueryOperator):
    """
    Method to generate a query for ranges of dielectric constant data
    """

    def query(
        self,
        e_total_max: Optional[float] = Query(
            None, description="Maximum value for the total dielectric constant.",
        ),
        e_total_min: Optional[float] = Query(
            None, description="Minimum value for the total dielectric constant.",
        ),
        e_ionic_max: Optional[float] = Query(
            None, description="Maximum value for the ionic dielectric constant.",
        ),
        e_ionic_min: Optional[float] = Query(
            None, description="Minimum value for the ionic dielectric constant.",
        ),
        e_electronic_max: Optional[float] = Query(
            None, description="Maximum value for the electronic dielectric constant.",
        ),
        e_electronic_min: Optional[float] = Query(
            None, description="Minimum value for the electronic dielectric constant.",
        ),
        n_max: Optional[float] = Query(
            None, description="Maximum value for the refractive index.",
        ),
        n_min: Optional[float] = Query(
            None, description="Minimum value for the refractive index.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "dielectric.e_total": [e_total_min, e_total_max],
            "dielectric.e_ionic": [e_ionic_min, e_ionic_max],
            "dielectric.e_electronic": [e_electronic_min, e_electronic_max],
            "dielectric.n": [n_min, n_max],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        keys = [
            "dielectric.e_total",
            "dielectric.e_ionic",
            "dielectric.e_electronic",
            "dielectric.n",
        ]
        return [(key, False) for key in keys]
