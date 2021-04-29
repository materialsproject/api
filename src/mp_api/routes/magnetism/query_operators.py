from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict

from mp_api.routes.magnetism.models import MagneticOrderingEnum


class MagneticQuery(QueryOperator):
    """
    Method to generate a query for magnetic data.
    """

    def query(
        self,
        ordering: Optional[MagneticOrderingEnum] = Query(
            None, description="Magnetic ordering of the material."
        ),
        total_magnetization_max: Optional[float] = Query(
            None, description="Maximum value for the total magnetization.",
        ),
        total_magnetization_min: Optional[float] = Query(
            None, description="Minimum value for the total magnetization.",
        ),
        total_magnetization_normalized_vol_max: Optional[float] = Query(
            None,
            description="Maximum value for the total magnetization normalized with volume.",
        ),
        total_magnetization_normalized_vol_min: Optional[float] = Query(
            None,
            description="Minimum value for the total magnetization normalized with volume.",
        ),
        total_magnetization_normalized_formula_units_max: Optional[float] = Query(
            None,
            description="Maximum value for the total magnetization normalized with formula units.",
        ),
        total_magnetization_normalized_formula_units_min: Optional[float] = Query(
            None,
            description="Minimum value for the total magnetization normalized with formula units.",
        ),
        num_magnetic_sites_max: Optional[int] = Query(
            None, description="Maximum value for the total number of magnetic sites.",
        ),
        num_magnetic_sites_min: Optional[int] = Query(
            None, description="Minimum value for the total number of magnetic sites.",
        ),
        num_unique_magnetic_sites_max: Optional[int] = Query(
            None,
            description="Maximum value for the total number of unique magnetic sites.",
        ),
        num_unique_magnetic_sites_min: Optional[int] = Query(
            None,
            description="Minimum value for the total number of unique magnetic sites.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "magnetism.total_magnetization": [
                total_magnetization_min,
                total_magnetization_max,
            ],
            "magnetism.total_magnetization_normalized_vol": [
                total_magnetization_normalized_vol_min,
                total_magnetization_normalized_vol_max,
            ],
            "magnetism.total_magnetization_normalized_formula_units": [
                total_magnetization_normalized_formula_units_min,
                total_magnetization_normalized_formula_units_max,
            ],
            "magnetism.num_magnetic_sites": [
                num_magnetic_sites_min,
                num_magnetic_sites_max,
            ],
            "magnetism.num_unique_magnetic_sites": [
                num_unique_magnetic_sites_min,
                num_unique_magnetic_sites_max,
            ],
        }  # type: dict

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        if ordering:
            crit["magnetism.ordering"] = ordering.value

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = self._keys_from_query()
        indexes = []
        for key in keys:
            if "_min" in key:
                key = key.replace("_min", "")
            indexes.append(("magnetism." + key, False))
        return indexes
