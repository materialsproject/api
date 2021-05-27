from typing import Optional
from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.routes.materials.utils import formula_to_criteria
from emmet.core.symmetry import CrystalSystem
from pymatgen.core.periodic_table import Element
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
    ) -> STORE_PARAMS:

        crit = {}

        if formula:
            crit.update(formula_to_criteria(formula))

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = ["chemsys", "formula_pretty", "formula_anonymous", "composition_reduced"]
        return [(key, False) for key in keys]


class ElementsQuery(QueryOperator):
    """
    Factory method to generate a dependency for querying by element data
    """

    def query(
        self,
        elements: Optional[str] = Query(
            None,
            description="Query by elements in the material composition as a comma-separated list",
        ),
        exclude_elements: Optional[str] = Query(
            None,
            description="Query by excluded elements in the material composition as a comma-separated list",
        ),
    ) -> STORE_PARAMS:

        crit = {}  # type: dict

        if elements or exclude_elements:
            crit["elements"] = {}

        if elements:
            element_list = [Element(e) for e in elements.strip().split(",")]
            crit["elements"]["$all"] = [str(el) for el in element_list]

        if exclude_elements:
            element_list = [Element(e) for e in exclude_elements.strip().split(",")]
            crit["elements"]["$nin"] = [str(el) for el in element_list]

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("elements", False)]


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
        nelements_max: Optional[float] = Query(
            None, description="Maximum value for the number of elements.",
        ),
        nelements_min: Optional[float] = Query(
            None, description="Minimum value for the number of elements.",
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

        crit = defaultdict(dict)  # type: dict

        entries = {
            "nsites": [nsites_min, nsites_max],
            "nelements": [nelements_min, nelements_max],
            "volume": [volume_min, volume_max],
            "density": [density_min, density_max],
        }  # type: dict

        for entry in entries:
            if entries[entry][0]:
                crit[entry]["$gte"] = entries[entry][0]

            if entries[entry][1]:
                crit[entry]["$lte"] = entries[entry][1]

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = self._keys_from_query()
        indexes = []
        for key in keys:
            if "_min" in key:
                key = key.replace("_min", "")
                indexes.append((key, False))
        return indexes


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

        crit = {}  # type: dict

        if crystal_system:
            crit.update({"symmetry.crystal_system": str(crystal_system.value)})

        if spacegroup_number:
            crit.update({"symmetry.number": spacegroup_number})

        if spacegroup_symbol:
            crit.update({"symmetry.symbol": spacegroup_symbol})

        return {"criteria": crit}

    def ensure_indexes(self):
        keys = ["symmetry.crystal_system", "symmetry.number", "symmetry.symbol"]
        return [(key, False) for key in keys]


class MultiTaskIDQuery(QueryOperator):
    """
    Method to generate a query for different task_ids
    """

    def query(
        self,
        task_ids: Optional[str] = Query(
            None, description="Comma-separated list of task_ids to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if task_ids:
            crit.update({"task_ids": {"$in": task_ids.split(",")}})

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("task_ids", False)]


class MultiMaterialIDQuery(QueryOperator):
    """
    Method to generate a query for different root-level material_id values
    """

    def query(
        self,
        material_ids: Optional[str] = Query(
            None, description="Comma-separated list of material_id values to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if material_ids:
            crit.update({"material_id": {"$in": material_ids.split(",")}})

        return {"criteria": crit}
