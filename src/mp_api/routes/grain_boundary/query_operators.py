from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict

from mp_api.routes.grain_boundary.models import GBTypeEnum


class GBStructureQuery(QueryOperator):
    """
    Method to generate a query for structure related data associated with grain boundary entries
    """

    def query(
        self,
        sigma: Optional[float] = Query(None, description="Value of sigma.",),
        type: Optional[GBTypeEnum] = Query(None, description="Grain boundary type.",),
        chemsys: Optional[str] = Query(
            None, description="Dash-delimited string of elements in the material.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if sigma:
            crit["sigma"] = sigma

        if type:
            crit["type"] = type.value

        if chemsys:
            chemsys = "-".join(sorted(chemsys.split("-")))
            crit["chemsys"] = chemsys

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
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
            crit.update(
                {
                    "task_id": {
                        "$in": [task_id.strip() for task_id in task_ids.split(",")]
                    }
                }
            )

        return {"criteria": crit}
