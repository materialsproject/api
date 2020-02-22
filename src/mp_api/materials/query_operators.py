from typing import Optional, Dict
from fastapi import Query
from maggma.core import Store
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.materials.utils import formula_to_criteria


class FormulaQuery(QueryOperator):
    """
    Factory method to generate a dependency for querying by formula with wild cards
    """

    def query(
        self,
        formula: Optional[str] = Query(
            None,
            description="Query by formula including anonymized formula or by including wild cards",
        ),
    ) -> STORE_PARAMS:
        """
        Pagination parameters for the API Endpoint
        """
        return {"criteria": formula_to_criteria(formula)} if formula else {}

    def meta(self, store: Store, query: Dict) -> Dict:
        """
        Metadata for the formula query operator

        Args:
            store: the Maggma Store that the resource uses
            query: the query being executed in this API call
        """
        elements = store.distinct("elements", criteria=query)
        return {"elements": elements}
