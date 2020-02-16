from typing import Optional
from fastapi import Query
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
