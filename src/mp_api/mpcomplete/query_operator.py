from typing import Dict
from fastapi import Query, Body
from pymatgen.core.structure import Structure
from mp_api.core.utils import STORE_PARAMS
from mp_api.core.query_operator import QueryOperator


class MPCompletePostQuery(QueryOperator):
    """Query operators to provide MPComplete data to post"""

    def query(
        self,
        structure: Structure = Body(..., title="Structure submission"),
        public_name: str = Query(..., title="Public name"),
        public_email: str = Query(..., title="Public email"),
        comment: str = Query(..., title="Submission comment"),
    ) -> STORE_PARAMS:

        self.structure = structure
        self.public_name = public_name
        self.public_email = public_email
        self.comment = comment

        crit = {
            "structure": structure,
            "public_email": public_email,
            "public_name": public_name,
            "comment": comment,
        }

        return {"criteria": crit}

    def post_process(self, written):

        d = [
            {
                "structure": self.structure,
                "public_email": self.public_email,
                "public_name": self.public_name,
                "comment": self.comment,
            }
        ]

        return d
