from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict

from mp_api.magnetism.models import MagneticOrderingEnum, TotalMagNormalizationEnum


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
            None,
            description="Maximum value for the total magnetization.",
        ),
        total_magnetization_min: Optional[float] = Query(
            None,
            description="Minimum value for the total magnetization.",
        ),
        total_magnetization_normalization: Optional[TotalMagNormalizationEnum] = Query(
            None,
            description="Type of normalization of the total magnetization values supplied.",
        ),
        num_magnetic_sites_max: Optional[int] = Query(
            None,
            description="Maximum value for the total number of magnetic sites.",
        ),
        num_magnetic_sites_min: Optional[int] = Query(
            None,
            description="Minimum value for the total number of magnetic sites.",
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

        mag = "magnetism.total_magnetization"

        if total_magnetization_normalization:
            if total_magnetization_normalization.value == "volume":
                mag = "magnetism.total_magnetization_normalized_vol"
            elif total_magnetization_normalization.value == "formula_units":
                mag = "magnetism.total_magnetization_normalized_formula_units"

        d = {
            mag: [
                total_magnetization_min,
                total_magnetization_max,
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
