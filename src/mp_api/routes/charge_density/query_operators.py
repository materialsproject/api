from fastapi import Query
from maggma.api.query_operator.core import QueryOperator
from maggma.api.utils import STORE_PARAMS


class ChgcarTaskIDQuery(QueryOperator):
    """
    Method to generate a query on CHGCAR data with calculation (task) ID
    """

    def query(
        self,
        task_ids: str = Query(
            None,
            description="Comma-separated list of calculation (task) IDs to query on",
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
