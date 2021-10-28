from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict

from pymatgen.analysis.magnetism import Ordering


class MagneticQuery(QueryOperator):
    """
    Method to generate a query for magnetic data.
    """

    def query(
        self,
        ordering: Optional[Ordering] = Query(
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
            "total_magnetization": [total_magnetization_min, total_magnetization_max],
            "total_magnetization_normalized_vol": [
                total_magnetization_normalized_vol_min,
                total_magnetization_normalized_vol_max,
            ],
            "total_magnetization_normalized_formula_units": [
                total_magnetization_normalized_formula_units_min,
                total_magnetization_normalized_formula_units_max,
            ],
            "num_magnetic_sites": [num_magnetic_sites_min, num_magnetic_sites_max],
            "num_unique_magnetic_sites": [
                num_unique_magnetic_sites_min,
                num_unique_magnetic_sites_max,
            ],
        }  # type: dict

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        if ordering:
            crit["ordering"] = ordering.value

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        keys = self._keys_from_query()
        indexes = []
        for key in keys:
            if "_min" in key:
                key = key.replace("_min", "")
                indexes.append((key, False))
        return indexes
