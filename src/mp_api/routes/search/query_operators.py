from enum import Enum
from typing import Optional
from fastapi import Query

from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from mp_api.routes.magnetism.models import MagneticOrderingEnum

from collections import defaultdict


class HasPropsEnum(Enum):
    magnetism = "magnetism"
    piezoelectric = "piezoelectric"
    dielectric = "dielectric"
    elasticity = "elasticity"
    surface_properties = "surface_properties"
    insertion_electrode = "insertion_electrode"
    bandstructure = "bandstructure"
    dos = "dos"
    xas = "xas"
    grain_boundaries = "grain_boundaries"
    eos = "eos"


class HasPropsQuery(QueryOperator):
    """
    Method to generate a query on whether a material has a certain property
    """

    def query(
        self,
        has_props: Optional[str] = Query(
            None,
            description="Comma-delimited list of possible properties given by HasPropsEnum to search for.",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if has_props:
            crit = {"has_props": {"$all": has_props.split(",")}}

        return {"criteria": crit}


class MaterialIDsSearchQuery(QueryOperator):
    """
    Method to generate a query on search docs using multiple material_id values
    """

    def query(
        self,
        material_ids: Optional[str] = Query(
            None, description="Comma-separated list of material_ids to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if material_ids:
            crit.update({"material_id": {"$in": material_ids.split(",")}})

        return {"criteria": crit}


class SearchIsStableQuery(QueryOperator):
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
        return [("is_stable", False)]


class SearchMagneticQuery(QueryOperator):
    """
    Method to generate a query for magnetic data in search docs.
    """

    def query(
        self,
        ordering: Optional[MagneticOrderingEnum] = Query(
            None, description="Magnetic ordering of the material."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if ordering:
            crit["ordering"] = ordering.value

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("ordering", False)]


class SearchIsTheoreticalQuery(QueryOperator):
    """
    Method to generate a query on whether a material is theoretical
    """

    def query(
        self,
        theoretical: Optional[bool] = Query(
            None, description="Whether the material is theoretical."
        ),
    ):

        crit = {}

        if theoretical is not None:
            crit["theoretical"] = theoretical

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("theoretical", False)]


# TODO:
# XAS and GB sub doc query operators
# Add weighted work function to data
# Add dimensionality to search endpoint
# Add "has_reconstructed" data
