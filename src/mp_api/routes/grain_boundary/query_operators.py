from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict
from pymatgen.core.composition import Composition

from mp_api.routes.grain_boundary.models import GBTypeEnum


class GBStructureQuery(QueryOperator):
    """
    Method to generate a query for structure related data associated with grain boundary entries
    """

    def query(
        self,
        sigma: Optional[int] = Query(None, description="Value of sigma.",),
        type: Optional[GBTypeEnum] = Query(None, description="Grain boundary type.",),
        chemsys: Optional[str] = Query(
            None, description="Dash-delimited string of elements in the material.",
        ),
        pretty_formula: Optional[str] = Query(
            None, description="Formula of the material.",
        ),
        gb_plane: Optional[str] = Query(
            None,
            description="Miller index of the grain boundary plane as comma delimitd integers.",
        ),
        rotation_axis: Optional[str] = Query(
            None,
            description="Miller index of the rotation axis as comma delimitd integers.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if sigma:
            crit["sigma"] = int(sigma)

        if type:
            crit["type"] = type.value

        if chemsys:
            chemsys = "-".join(sorted(chemsys.split("-")))
            crit["chemsys"] = chemsys

        if pretty_formula:
            crit["pretty_formula"] = Composition(pretty_formula).reduced_formula

        if gb_plane:
            crit["gb_plane"] = [int(n.strip()) for n in gb_plane.split(",")]

        if rotation_axis:
            crit["rotation_axis"] = [int(n.strip()) for n in rotation_axis.split(",")]

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
