from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict


class SubstrateStructureQuery(QueryOperator):
    """
    Method to generate a query for film and substrate data.
    """

    def query(
        self,
        film_id: Optional[str] = Query(None, description="Materials Project ID of the film material.",),
        substrate_id: Optional[str] = Query(None, description="Materials Project ID of the substrate material.",),
        substrate_formula: Optional[str] = Query(None, description="Reduced formula of the substrate material.",),
        film_orientation: Optional[str] = Query(
            None, description="Comma separated integers defining the film surface orientation.",
        ),
        substrate_orientation: Optional[str] = Query(
            None, description="Comma separated integers defining the substrate surface orientation.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if film_id:
            crit["film_id"] = film_id

        if substrate_id:
            crit["sub_id"] = substrate_id

        if substrate_formula:
            crit["sub_form"] = substrate_formula

        if film_orientation:
            crit["film_orient"] = film_orientation.replace(",", " ")

        if substrate_orientation:
            crit["orient"] = substrate_orientation.replace(",", " ")

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = ["film_id", "sub_id", "sub_form", "film_orient", "orient"]
        return [(key, False) for key in keys]


class EnergyAreaQuery(QueryOperator):
    """
    Method to generate a query for ranges of substrate
    elastic energies and minimum coincident areas.
    """

    def query(
        self,
        area_max: Optional[float] = Query(
            None, description="Maximum value for the minimum coincident interface area in Å².",
        ),
        area_min: Optional[float] = Query(
            None, description="Minimum value for the minimum coincident interface area in Å².",
        ),
        energy_max: Optional[float] = Query(None, description="Maximum value for the energy in meV.",),
        energy_min: Optional[float] = Query(None, description="Minimum value for the energy in meV.",),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "area": [area_min, area_max],
            "energy": [energy_min, energy_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = ["area", "energy"]
        return [(key, False) for key in keys]
