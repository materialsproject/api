from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict


class BondLengthQuery(QueryOperator):
    """
    Method to generate a query on bond length data.
    """

    def query(
        self,
        max_bond_length_max: Optional[float] = Query(
            None,
            description="Maximum value for the maximum bond length in the structure.",
        ),
        max_bond_length_min: Optional[float] = Query(
            None,
            description="Minimum value for the maximum bond length in the structure.",
        ),
        min_bond_length_max: Optional[float] = Query(
            None,
            description="Maximum value for the minimum bond length in the structure.",
        ),
        min_bond_length_min: Optional[float] = Query(
            None,
            description="Minimum value for the minimum bond length in the structure.",
        ),
        mean_bond_length_max: Optional[float] = Query(
            None,
            description="Maximum value for the mean bond length in the structure.",
        ),
        mean_bond_length_min: Optional[float] = Query(
            None,
            description="Minimum value for the mean bond length in the structure.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "bond_length_stats.max": [max_bond_length_min, max_bond_length_max],
            "bond_length_stats.min": [min_bond_length_min, min_bond_length_max],
            "bond_length_stats.mean": [mean_bond_length_min, mean_bond_length_max],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        keys = [
            "bond_length_stats.max",
            "bond_length_stats.min",
            "bond_length_stats.mean",
        ]
        return [(key, False) for key in keys]


class CoordinationEnvsQuery(QueryOperator):
    """
    Method to generate a query on coordination environment data.
    """

    def query(
        self,
        coordination_envs: Optional[str] = Query(
            None,
            description="Query by coordination environments in the material composition as a comma-separated list\
 (e.g. 'Mo-S(6),S-Mo(3)')",
        ),
        coordination_envs_anonymous: Optional[str] = Query(
            None,
            description="Query by anonymous coordination environments in the material composition as a comma-separated\
 list (e.g. 'A-B(6),A-B(3)')",
        ),
    ) -> STORE_PARAMS:

        crit = {}  # type: dict

        if coordination_envs:
            env_list = [env.strip() for env in coordination_envs.split(",")]
            crit["coordination_envs"] = {"$all": [str(env) for env in env_list]}

        if coordination_envs_anonymous:
            env_list = [env.strip() for env in coordination_envs_anonymous.split(",")]
            crit["coordination_envs_anonymous"] = {
                "$all": [str(env) for env in env_list]
            }

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("coordination_envs", False), ("coordination_envs_anonymous", False)]
