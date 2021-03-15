from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from fastapi import Query
from typing import Optional


class MultipleTaskIDsQuery(QueryOperator):
    """
    Method to generate a query on search docs using multiple task_id values
    """

    def query(
        self,
        task_ids: Optional[str] = Query(
            None, description="Comma-separated list of task_ids to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if task_ids:
            crit.update({"task_id": {"$in": task_ids.split(",")}})

        return {"criteria": crit}
