from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.materials.utils import formula_to_criteria
from mp_api.materials.models.core import CrystalSystem
from pymatgen import Element
from collections import defaultdict


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

        crit = {}

        if formula:
            crit.update(formula_to_criteria(formula))

        if elements:
            element_list = [Element(e) for e in elements.strip().split(",")]
            crit["elements"] = {"$all": [str(el) for el in element_list]}

        return {"criteria": crit}


class DeprecationQuery(QueryOperator):
    """
    Method to generate a deprecation state query
    """

    def query(
        self,
        deprecated: Optional[bool] = Query(
            None, description="Whether the material is marked as deprecated",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if deprecated:
            crit.update({"deprecated": deprecated})

        return {"criteria": crit}


class MinMaxQuery(QueryOperator):
    """
    Method to generate a query for quantities with a definable min and max
    """

    def query(
        self,
        nsites_max: Optional[int] = Query(
            None, description="Maximum value for the number of sites",
        ),
        nsites_min: Optional[int] = Query(
            None, description="Minimum value for the number of sites",
        ),
        volume_max: Optional[float] = Query(
            None, description="Maximum value for the cell volume",
        ),
        volume_min: Optional[float] = Query(
            None, description="Minimum value for the cell volume",
        ),
        density_max: Optional[float] = Query(
            None, description="Maximum value for the density",
        ),
        density_min: Optional[float] = Query(
            None, description="Minimum value for the density",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)

        d = {
            "nsites": [nsites_min, nsites_max],
            "volume": [volume_min, volume_max],
            "density": [density_min, density_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry] = {"$gte": d[entry][0]}

            if d[entry][1]:
                crit[entry] = {"$lte": d[entry][1]}

        return {"criteria": crit}


class SymmetryQuery(QueryOperator):
    """
    Method to generate a query on symmetry information
    """

    def query(
        self,
        crystal_system: Optional[CrystalSystem] = Query(
            None, description="Crystal system of the material",
        ),
        spacegroup_number: Optional[int] = Query(
            None, description="Space group number of the material",
        ),
        spacegroup_symbol: Optional[str] = Query(
            None, description="Space group symbol of the material",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if crystal_system:
            crit.update({"symmetry.crystal_system": str(crystal_system.value)})

        if spacegroup_number:
            crit.update({"symmetry.number": spacegroup_number})

        if spacegroup_symbol:
            crit.update({"symmetry.symbol": spacegroup_symbol})

        return {"criteria": crit}
