from maggma.api.resource import SubmissionResource
from mp_api.routes._general_store.query_operator import (
    GeneralStorePostQuery,
    GeneralStoreGetQuery,
)
from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.routes._general_store.models import GeneralStoreDoc


def general_store_resource(general_store):
    resource = SubmissionResource(
        general_store,
        GeneralStoreDoc,
        post_query_operators=[GeneralStorePostQuery()],
        get_query_operators=[
            GeneralStoreGetQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                model=GeneralStoreDoc,
                default_fields=["kind", "markdown", "meta", "last_updated"],
            ),
        ],
        enable_default_search=True,
        include_in_schema=False,
        calculate_submission_id=True,
    )

    return resource
