from typing import Optional

import numpy as np
from emmet.core.search import SearchDoc
from fastapi import Query
from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.core.resource import GetResource
from mp_api.routes.electronic_structure.query_operators import ESSummaryDataQuery
from mp_api.routes.materials.query_operators import (
    DeprecationQuery,
    ElementsQuery,
    FormulaQuery,
    SymmetryQuery,
)
from mp_api.routes.search.models import SearchStats
from mp_api.routes.search.query_operators import (
    HasPropsQuery,
    MaterialIDsSearchQuery,
    SearchDielectricPiezoQuery,
    SearchElasticityQuery,
    SearchIsStableQuery,
    SearchIsTheoreticalQuery,
    SearchMagneticQuery,
)
from mp_api.routes.surface_properties.query_operators import SurfaceMinMaxQuery
from mp_api.routes.thermo.query_operators import ThermoEnergyQuery
from scipy.stats import gaussian_kde
from typing_extensions import Literal


def search_resource(search_store):
    resource = ReadOnlyResource(
        search_store,
        SearchDoc,
        query_operators=[
            MaterialIDsSearchQuery(),
            FormulaQuery(),
            ElementsQuery(),
            SymmetryQuery(),
            SearchIsStableQuery(),
            SearchIsTheoreticalQuery(),
            SearchMagneticQuery(),
            NumericQuery(model=SearchDoc, excluded_fields=["composition"]),
            HasPropsQuery(),
            DeprecationQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SearchDoc, default_fields=["material_id"]),
        ],
        tags=["Search"],
    )

    return resource


def search_stats_resource(search_store):
    resource = AggregationResource(
        search_store,
        SearchStats,
        pipeline_query_operator=SearchStatsQuery(SearchDoc),
        tags=["Search"],
        sub_path="/stats/",
    )

    return resource
