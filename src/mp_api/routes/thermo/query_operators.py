from typing import Optional
from collections import defaultdict
from fastapi import Query
from pymatgen.core import Element
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS


class ThermoChemicalQuery(QueryOperator):
    """
    Method to generate a query on chemical data associated with a thermo doc
    """

    def query(
        self,
        chemsys: Optional[str] = Query(
            None, description="Dash-delimited list of elements in the material.",
        ),
        elements: Optional[str] = Query(
            None,
            description="Elements in the material composition as a comma-separated list",
        ),
        nelements: Optional[int] = Query(
            None, description="Number of elements in the material",
        ),
    ):

        crit = {}  # type: dict

        if chemsys:
            eles = chemsys.split("-")
            chemsys = "-".join(sorted(eles))

            crit["chemsys"] = chemsys

        if elements:
            element_list = [Element(e) for e in elements.strip().split(",")]
            crit["elements"] = {"$all": [str(el) for el in element_list]}

        if nelements:
            crit["nelements"] = nelements

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = self._keys_from_query()
        return [(key, False) for key in keys]


class IsStableQuery(QueryOperator):
    """
    Method to generate a query on whether a material is stable
    """

    def query(
        self,
        is_stable: Optional[bool] = Query(
            None, description="Whether the material is stable."
        ),
    ):

        crit = {}

        if is_stable is not None:
            crit["is_stable"] = is_stable

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = self._keys_from_query()
        return [(key, False) for key in keys]
