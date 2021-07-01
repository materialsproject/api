from fastapi import Query, Body
from pymatgen.core.structure import Structure
from maggma.api.utils import STORE_PARAMS
from maggma.api.query_operator import QueryOperator
from uuid import uuid4


class MPCompletePostQuery(QueryOperator):
    """Query operators to provide MPComplete data to post"""

    def query(
        self,
        structure: Structure = Body(..., title="Structure submission"),
        public_name: str = Query(..., title="Public name"),
        public_email: str = Query(..., title="Public email"),
    ) -> STORE_PARAMS:

        self.structure = structure
        self.public_name = public_name
        self.public_email = public_email

        crit = {
            "structure": structure,
            "public_email": public_email,
            "public_name": public_name,
        }

        return {"criteria": crit}

    def post_process(self, written):

        d = [
            {
                "structure": self.structure,
                "public_email": self.public_email,
                "public_name": self.public_name,
            }
        ]

        return d


class MPCompleteGetQuery(QueryOperator):
    """Query operators for querying on MPComplete data"""

    def query(
        self,
        public_name: str = Query(None, title="Public name"),
        public_email: str = Query(None, title="Public email"),
    ) -> STORE_PARAMS:

        self.public_name = public_name
        self.public_email = public_email

        crit = {}

        if public_name is not None:
            crit.update({"public_name": public_name})

        if public_email is not None:
            crit.update({"public_email": public_email})

        return {"criteria": crit}
