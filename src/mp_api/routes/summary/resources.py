from emmet.core.summary import SummaryDoc

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
from mp_api.routes.oxidation_states.query_operators import PossibleOxiStateQuery
from emmet.core.summary import SummaryStats
from mp_api.routes.summary.query_operators import (
    HasPropsQuery,
    MaterialIDsSearchQuery,
    SearchIsStableQuery,
    SearchIsTheoreticalQuery,
    SearchMagneticQuery,
    SearchHasReconstructedQuery,
    SearchStatsQuery,
    SearchESQuery,
)


def summary_resource(summary_store):
    resource = ReadOnlyResource(
        summary_store,
        SummaryDoc,
        query_operators=[
            MaterialIDsSearchQuery(),
            FormulaQuery(),
            ElementsQuery(),
            PossibleOxiStateQuery(),
            SymmetryQuery(),
            SearchIsStableQuery(),
            SearchIsTheoreticalQuery(),
            SearchMagneticQuery(),
            SearchESQuery(),
            NumericQuery(model=SummaryDoc, excluded_fields=["composition"]),
            SearchHasReconstructedQuery(),
            HasPropsQuery(),
            DeprecationQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SummaryDoc, default_fields=["material_id"]),
        ],
        tags=["Summary"],
        disable_validation=True,
    )

    return resource


def summary_stats_resource(summary_store):
    resource = AggregationResource(
        summary_store,
        SummaryStats,
        pipeline_query_operator=SearchStatsQuery(SummaryDoc),
        tags=["Summary"],
        sub_path="/stats/",
    )

    return resource
