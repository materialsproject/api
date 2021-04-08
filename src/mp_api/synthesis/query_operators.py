from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from pymatgen.core import Composition

from collections import defaultdict


class SynthFormulaQuery(QueryOperator):
    """
    Method to generate a query for synthesis data using a chemical formula
    """

    def query(
        self,
        formula: Optional[str] = Query(
            None, description="Chemical formula of the material.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if formula:

            reduced_formula = Composition(formula).get_reduced_formula_and_factor()[0]
            crit["formula"] = reduced_formula

        return {"criteria": crit}

    def ensure_indices(self):
        return [("formula", False)]
