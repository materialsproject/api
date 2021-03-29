from typing import Dict
from fastapi import Query, Body
from mp_api.core.utils import STORE_PARAMS
from mp_api.core.query_operator import QueryOperator


class UserSettingsQuery(QueryOperator):
    """Query operators to provide user settings information"""

    def query(
        self,
        consumer_id: str = Query(..., title="Consumer ID",),
        settings: Dict = Body(..., title="User settings",),
    ) -> STORE_PARAMS:

        self.cid = consumer_id

        crit = {"consumer_id": consumer_id, "settings": settings}

        return {"criteria": crit}

    def post_process(self, written):

        d = [{"consumer_id": self.cid, "successful": False}]

        if written:
            d = [{"consumer_id": self.cid, "successful": True}]

        return d
