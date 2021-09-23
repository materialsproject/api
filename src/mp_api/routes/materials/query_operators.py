from itertools import permutations
from typing import Optional

from emmet.core.symmetry import CrystalSystem
from fastapi import Body, HTTPException, Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from mp_api.routes.materials.utils import formula_to_criteria
from pymatgen.analysis.structure_matcher import ElementComparator, StructureMatcher
from pymatgen.core.composition import Composition, CompositionError
from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Structure


class FormulaQuery(QueryOperator):
    """
    Factory method to generate a dependency for querying by
        formula or chemical system with wild cards.
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

    def ensure_indexes(self):  # pragma: no cover
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

    def ensure_indexes(self):  # pragma: no cover
        return [("elements", False)]


class DeprecationQuery(QueryOperator):
    """
    Method to generate a deprecation state query
    """

    def query(
        self,
        deprecated: Optional[bool] = Query(
            False, description="Whether the material is marked as deprecated",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if deprecated is not None:
            crit.update({"deprecated": deprecated})

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

        crit = {}  # type: dict

        if crystal_system:
            crit.update({"symmetry.crystal_system": str(crystal_system.value)})

        if spacegroup_number:
            crit.update({"symmetry.number": spacegroup_number})

        if spacegroup_symbol:
            crit.update({"symmetry.symbol": spacegroup_symbol})

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
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
            crit.update(
                {
                    "task_ids": {
                        "$in": [task_id.strip() for task_id in task_ids.split(",")]
                    }
                }
            )

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
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
            crit.update(
                {
                    "material_id": {
                        "$in": [
                            material_id.strip()
                            for material_id in material_ids.split(",")
                        ]
                    }
                }
            )

        return {"criteria": crit}


class FindStructureQuery(QueryOperator):
    """
    Method to generate a find structure query
    """

    def query(
        self,
        structure: Structure = Body(
            ..., description="Pymatgen structure object to query with",
        ),
        ltol: float = Query(
            0.2, description="Fractional length tolerance. Default is 0.2.",
        ),
        stol: float = Query(
            0.3,
            description="Site tolerance. Defined as the fraction of the average free \
                    length per atom := ( V / Nsites ) ** (1/3). Default is 0.3.",
        ),
        angle_tol: float = Query(
            5, description="Angle tolerance in degrees. Default is 5 degrees.",
        ),
        limit: int = Query(
            1,
            description="Maximum number of matches to show. Defaults to 1, only showing the best match.",
        ),
    ) -> STORE_PARAMS:

        self.ltol = ltol
        self.stol = stol
        self.angle_tol = angle_tol
        self.limit = limit
        self.structure = structure

        crit = {}

        try:
            s = Structure.from_dict(structure)
        except Exception:
            raise HTTPException(
                status_code=404,
                detail="Body cannot be converted to a pymatgen structure object.",
            )

        crit.update({"composition_reduced": dict(s.composition.to_reduced_dict)})

        return {"criteria": crit}

    def post_process(self, docs):

        s1 = Structure.from_dict(self.structure)

        m = StructureMatcher(
            ltol=self.ltol,
            stol=self.stol,
            angle_tol=self.angle_tol,
            primitive_cell=True,
            scale=True,
            attempt_supercell=False,
            comparator=ElementComparator(),
        )

        matches = []

        for doc in docs:

            s2 = Structure.from_dict(doc["structure"])
            matched = m.fit(s1, s2)

            if matched:
                rms = m.get_rms_dist(s1, s2)

                matches.append(
                    {
                        "material_id": doc["material_id"],
                        "normalized_rms_displacement": rms[0],
                        "max_distance_paired_sites": rms[1],
                    }
                )

        response = sorted(
            matches[: self.limit],
            key=lambda x: (
                x["normalized_rms_displacement"],
                x["max_distance_paired_sites"],
            ),
        )

        return response

    def ensure_indexes(self):  # pragma: no cover
        return [("composition_reduced", False)]


class FormulaAutoCompleteQuery(QueryOperator):
    """
    Method to generate a formula autocomplete query
    """

    def query(
        self,
        formula: str = Query(..., description="Human readable chemical formula.",),
        limit: int = Query(
            10, description="Maximum number of matches to show. Defaults to 10.",
        ),
    ) -> STORE_PARAMS:

        self.formula = formula
        self.limit = limit

        try:
            comp = Composition(formula)
        except CompositionError:
            raise HTTPException(
                status_code=400, detail="Invalid formula provided.",
            )

        ind_str = []
        eles = []

        if len(comp) == 1:
            d = comp.get_integer_formula_and_factor()

            s = d[0] + str(int(d[1])) if d[1] != 1 else d[0]

            ind_str.append(s)
            eles.append(d[0])
        else:

            comp_red = comp.reduced_composition.items()

            for (i, j) in comp_red:

                if j != 1:
                    ind_str.append(i.name + str(int(j)))
                else:
                    ind_str.append(i.name)

                eles.append(i.name)

        final_terms = ["".join(entry) for entry in permutations(ind_str)]

        pipeline = [
            {
                "$search": {
                    "index": "formula_autocomplete",
                    "text": {"path": "formula_pretty", "query": final_terms},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "formula_pretty": 1,
                    "elements": 1,
                    "length": {"$strLenCP": "$formula_pretty"},
                }
            },
            {
                "$match": {
                    "length": {"$gte": len(final_terms[0])},
                    "elements": {"$all": eles},
                }
            },
            {"$limit": limit},
            {"$sort": {"length": 1}},
            {"$project": {"elements": 0, "length": 0}},
        ]

        return {"pipeline": pipeline}

    def ensure_indexes(self):  # pragma: no cover
        return [("formula_pretty", False)]
