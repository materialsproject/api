from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict


class SurfaceMinMaxQuery(QueryOperator):
    """
    Method to generate a query for ranges of surface energy, anisotropy, and shape factor.
    """

    def query(
        self,
        weighted_surface_energy_max: Optional[float] = Query(
            None, description="Maximum value for the weighted surface energy in J/m².",
        ),
        weighted_surface_energy_min: Optional[float] = Query(
            None, description="Minimum value for the weighted surface energy in J/m².",
        ),
        weighted_work_function_max: Optional[float] = Query(
            None, description="Maximum value for the weighted work function in eV.",
        ),
        weighted_work_function_min: Optional[float] = Query(
            None, description="Minimum value for the weighted work function in eV.",
        ),
        surface_anisotropy_max: Optional[float] = Query(
            None, description="Maximum value for the surface energy anisotropy.",
        ),
        surface_anisotropy_min: Optional[float] = Query(
            None, description="Minimum value for the surface energy anisotropy.",
        ),
        shape_factor_max: Optional[float] = Query(
            None, description="Maximum value for the shape factor.",
        ),
        shape_factor_min: Optional[float] = Query(
            None, description="Minimum value for the shape factor.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "weighted_surface_energy": [
                weighted_surface_energy_min,
                weighted_surface_energy_max,
            ],
            "weighted_work_function": [
                weighted_work_function_min,
                weighted_work_function_max,
            ],
            "surface_anisotropy": [surface_anisotropy_min, surface_anisotropy_max],
            "shape_factor": [shape_factor_min, shape_factor_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indices(self):
        keys = [
            "weighted_surface_energy",
            "weighted_work_function",
            "surface_anisotropy",
            "shape_factor",
        ]
        return [(key, False) for key in keys]


class ReconstructedQuery(QueryOperator):
    """
    Method to generate a query on whether the entry
    contains a reconstructed surface.
    """

    def query(
        self,
        has_reconstructed: Optional[bool] = Query(
            None, description="Whether the entry has a reconstructed surface.",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if has_reconstructed:
            crit.update({"has_reconstructed": has_reconstructed})

        return {"criteria": crit}

    def ensure_indices(self):
        return [("has_reconstructed", False)]
