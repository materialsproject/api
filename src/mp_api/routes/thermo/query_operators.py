from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator


class IsStableQuery(QueryOperator):
    """
    Method to generate a query on whether a material is stable
    """

    def query(
        self,
        is_stable: Optional[bool] = Query(
            None, description="Whether the material is stable."
        ),
    ):

        crit = {}

        if is_stable is not None:
            crit["is_stable"] = is_stable

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        keys = self._keys_from_query()
        return [(key, False) for key in keys]
