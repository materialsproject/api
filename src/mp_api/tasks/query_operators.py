from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator


class SingleTaskIDQuery(QueryOperator):
    """
    Method to generate a query for different task_ids
    """

    def query(
        self, task_id: str = Query(None, description="Single task_id to query on"),
    ) -> STORE_PARAMS:

        crit = {"task_id": task_id}

        return {"criteria": crit}
