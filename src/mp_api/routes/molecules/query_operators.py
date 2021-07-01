from typing import Optional
from fastapi import Query
from pymatgen.core.periodic_table import Element
from pymatgen.core import Composition
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict


class MoleculeElementsQuery(QueryOperator):
    """
    Method to generate a query on molecules using a list of elements
    """

    def query(
        self,
        elements: Optional[str] = Query(
            None,
            description="Query by elements in the material composition as a comma-separated list",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if elements:
            element_list = [Element(e.strip()) for e in elements.split(",")]
            crit["elements"] = {"$all": [str(el) for el in element_list]}

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("elements", False)]


class MoleculeBaseQuery(QueryOperator):
    """
    Method to generate a query over molecule data.
    """

    def query(
        self,
        nelements_max: Optional[float] = Query(
            None, description="Maximum value for the number of elements.",
        ),
        nelements_min: Optional[float] = Query(
            None, description="Minimum value for the number of elements.",
        ),
        EA_max: Optional[float] = Query(
            None, description="Maximum value for the electron affinity in eV.",
        ),
        EA_min: Optional[float] = Query(
            None, description="Minimum value for the electron affinity in eV.",
        ),
        IE_max: Optional[float] = Query(
            None, description="Maximum value for the ionization energy in eV.",
        ),
        IE_min: Optional[float] = Query(
            None, description="Minimum value for the ionization energy in eV.",
        ),
        charge_max: Optional[int] = Query(
            None, description="Maximum value for the charge in +e.",
        ),
        charge_min: Optional[int] = Query(
            None, description="Minimum value for the charge in +e.",
        ),
        pointgroup: Optional[str] = Query(
            None, description="Point of the molecule in Schoenflies notation.",
        ),
        smiles: Optional[str] = Query(
            None,
            description="The simplified molecular input line-entry system (SMILES) \
            representation of the molecule.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "nelements": [nelements_min, nelements_max],
            "EA": [EA_min, EA_max],
            "IE": [IE_min, IE_max],
            "charge": [charge_min, charge_max],
        }  # type: dict

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        if pointgroup:
            crit["pointgroup"] = pointgroup

        if smiles:
            crit["smiles"] = smiles

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        keys = self._keys_from_query()
        indexes = []
        for key in keys:
            if "_min" in key:
                key = key.replace("_min", "")
                indexes.append((key, False))
        return indexes


class MoleculeFormulaQuery(QueryOperator):
    """
    Method to generate a query for molecule data using a chemical formula
    """

    def query(
        self,
        formula: Optional[str] = Query(
            None, description="Chemical formula of the molecule.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if formula:

            reduced_formula = Composition(formula).get_reduced_formula_and_factor()[0]
            crit["formula_pretty"] = reduced_formula

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("formula_pretty", False)]
