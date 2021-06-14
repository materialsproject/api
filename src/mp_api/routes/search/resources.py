from typing import Optional
from typing_extensions import Literal
from maggma.api.query_operator.dynamic import NumericQuery

import numpy as np
from fastapi import Query
from scipy.stats import gaussian_kde

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from maggma.api.resource import ReadOnlyResource, AggregationResource
from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
    SymmetryQuery,
    DeprecationQuery,
)
from mp_api.routes.search.models import SearchDoc, SearchStats
from mp_api.routes.search.query_operators import (
    MaterialIDsSearchQuery,
    HasPropsQuery,
    SearchIsStableQuery,
    SearchIsTheoreticalQuery,
    SearchMagneticQuery,
    SearchStatsQuery,
)


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
