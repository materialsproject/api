from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict


class PossibleOxiStateQuery(QueryOperator):
    """
    Method to generate a query for possible oxidation state data.
    """

    def query(
        self,
        possible_species: str = Query(
            None,
            description="Comma delimited list of element symbols appended with oxidation states. \
                (e.g. Cr2+,O2-)",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if possible_species:
            crit["possible_species"] = {
                "$all": [specie.strip() for specie in possible_species.split(",")]
            }

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        keys = ["possible_species"]
        return [(key, False) for key in keys]
