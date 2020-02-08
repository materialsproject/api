from typing import Optional, Callable
from fastapi import Query
from mp_api.core.dependencies import STORE_PARAMS
from mp_api.materials.utils import formula_to_criteria


def formula_query_factory() -> Callable[..., STORE_PARAMS]:
    """
    Factory method to generate a dependency for querying by formula with wild cards

    Args:
        default_skip: default number of items to skip
        default_limit: default number of items to return
        max_limit: max number of items to return
    """

    def query(
        formula: Optional[str] = Query(
            None,
            description="Query by formula including anonymized formula or by including wild cards",
        )
    ) -> STORE_PARAMS:
        """
        Pagination parameters for the API Endpoint
        """
        return {"criteria": formula_to_criteria(formula)} if formula else {}

    return query
