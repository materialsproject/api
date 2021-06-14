from maggma.api.resource import ReadOnlyResource, AggregationResource
from mp_api.routes.synthesis.models import SynthesisDoc

from mp_api.routes.synthesis.query_operators import (
    SynthFormulaQuery,
    SynthesisTextSearchQuery,
)
from maggma.api.query_operator import SortQuery, PaginationQuery, SparseFieldsQuery


def synth_search_resource(synth_store):
    resource = AggregationResource(
        synth_store,
        SynthesisDoc,
        pipeline_query_operator=SynthesisTextSearchQuery(),
        tags=["Synthesis"],
        sub_path="/text_search/",
    )
    return resource


def synth_resource(synth_store):
    resource = ReadOnlyResource(
        synth_store,
        SynthesisDoc,
        query_operators=[
            SynthFormulaQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SynthesisDoc, default_fields=["formula", "doi"]),
        ],
        tags=["Synthesis"],
        enable_default_search=True,
        enable_get_by_key=False,
    )

    return resource
