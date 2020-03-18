from typing import Optional, Dict
from fastapi import Query
from maggma.core import Store
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.materials.utils import formula_to_criteria
from pymatgen import Element


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
        elements: Optional[str] = Query(
            None,
            description="Query by elements in the material composition as a comma-separated list",
        ),
    ) -> STORE_PARAMS:
        """
        Pagination parameters for the API Endpoint
        """
        crit = {}

        if formula:
            crit.update(formula_to_criteria(formula))

        if elements:
            element_list = [Element(e) for e in elements.strip().split(",")]
            crit["elements"] = {"$all": [str(el) for el in element_list]}

        return {"criteria": crit}

    def meta(self, store: Store, query: Dict) -> Dict:
        """
        Metadata for the formula query operator

        Args:
            store: the Maggma Store that the resource uses
            query: the query being executed in this API call
        """
        elements = store.distinct("elements", criteria=query)
        return {"elements": elements}
