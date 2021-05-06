from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict

from mp_api.routes.grain_boundary.models import GBTypeEnum


class GBEnergyQuery(QueryOperator):
    """
    Method to generate a query for energy values associated with grain boundary data
    """

    def query(
        self,
        gb_energy_max: Optional[float] = Query(
            None, description="Maximum value for the grain boundary energy in J/m^2.",
        ),
        gb_energy_min: Optional[float] = Query(
            None, description="Minimum value for the grain boundary energy in J/m^2.",
        ),
        w_sep_energy_max: Optional[float] = Query(
            None,
            description="Maximum value for the work of separation energy in J/m^2.",
        ),
        w_sep_energy_min: Optional[float] = Query(
            None, description="Minimum value for work of separation energy in J/m^2.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "gb_energy": [gb_energy_min, gb_energy_max],
            "w_sep": [w_sep_energy_min, w_sep_energy_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = ["gb_energy", "w_sep"]
        return [(key, False) for key in keys]


class GBStructureQuery(QueryOperator):
    """
    Method to generate a query for structure related data associated with grain boundary entries
    """

    def query(
        self,
        rotation_angle_max: Optional[float] = Query(
            None, description="Maximum value for the rotation angle in degrees.",
        ),
        rotation_angle_min: Optional[float] = Query(
            None, description="Minimum value for the rotation angle in degrees.",
        ),
        sigma: Optional[float] = Query(None, description="Value of sigma.",),
        type: Optional[GBTypeEnum] = Query(None, description="Grain boundary type.",),
        chemsys: Optional[str] = Query(
            None, description="Dash-delimited string of elements in the material.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "rotation_angle": [rotation_angle_min, rotation_angle_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry] = {"$gte": d[entry][0]}

            if d[entry][1]:
                crit[entry] = {"$lte": d[entry][1]}

        if sigma:
            crit["sigma"] = sigma

        if type:
            crit["type"] = type.value

        if chemsys:
            crit["chemsys"] = chemsys

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = [key for key in self._keys_from_query() if "_min" not in key]
        keys.append("rotation_angle")
        return [(key, False) for key in keys]


class GBTaskIDQuery(QueryOperator):
    """
    Method to generate a query for different task_ids
    """

    def query(
        self,
        task_ids: Optional[str] = Query(
            None,
            description="Comma-separated list of Materials Project IDs to query on.",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if task_ids:
            crit.update({"task_id": {"$in": task_ids.split(",")}})

        return {"criteria": crit}
