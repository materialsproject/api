from emmet.core.search import SearchDoc

from maggma.api.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
    NumericQuery,
)
from maggma.api.resource import ReadOnlyResource, AggregationResource
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
    SearchIsStableQuery,
    SearchIsTheoreticalQuery,
    SearchMagneticQuery,
    SearchStatsQuery,
    SearchESQuery,
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
            SearchESQuery(),
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
