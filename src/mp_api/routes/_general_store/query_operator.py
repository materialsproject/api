from typing import Dict
from fastapi import Query, Body
from maggma.api.utils import STORE_PARAMS
from maggma.api.query_operator import QueryOperator


class GeneralStorePostQuery(QueryOperator):
    """Query operators to provide general store information to post"""

    def query(
        self,
        kind: str = Query(..., title="Data type"),
        markdown: str = Query(None, title="Markdown data"),
        meta: Dict = Body(None, title="Metadata"),
    ) -> STORE_PARAMS:

        self.kind = kind
        self.markdown = markdown
        self.metadata = meta

        crit = {"kind": kind, "markdown": markdown, "meta": meta}

        return {"criteria": crit}

    def post_process(self, written):

        d = [{"kind": self.kind, "markdown": self.markdown, "meta": self.metadata}]

        return d


class GeneralStoreGetQuery(QueryOperator):
    """Query operators to obtain general store information"""

    def query(self, kind: str = Query(..., title="Data type")) -> STORE_PARAMS:

        crit = {"kind": kind}

        return {"criteria": crit}
