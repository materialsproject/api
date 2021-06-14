from typing import Dict
from fastapi import Query, Body
from maggma.api.utils import STORE_PARAMS
from maggma.api.query_operator import QueryOperator


class UserSettingsPostQuery(QueryOperator):
    """Query operators to provide user settings information to post"""

    def query(
        self,
        consumer_id: str = Query(..., title="Consumer ID",),
        settings: Dict = Body(..., title="User settings",),
    ) -> STORE_PARAMS:

        self.cid = consumer_id
        self.settings = settings

        crit = {"consumer_id": consumer_id, "settings": settings}

        return {"criteria": crit}

    def post_process(self, written):

        d = [{"consumer_id": self.cid, "settings": self.settings}]

        return d


class UserSettingsGetQuery(QueryOperator):
    """Query operators to provide user settings information"""

    def query(
        self, consumer_id: str = Query(..., title="Consumer ID",),
    ) -> STORE_PARAMS:

        crit = {"consumer_id": consumer_id}

        return {"criteria": crit}
