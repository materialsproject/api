from maggma.api.resource import SubmissionResource
from mp_api.routes._general_store.query_operator import (
    GeneralStorePostQuery,
    GeneralStoreGetQuery,
)
from mp_api.routes._general_store.models import GeneralStoreDoc


def general_store_resource(general_store):
    resource = SubmissionResource(
        general_store,
        GeneralStoreDoc,
        post_query_operators=[GeneralStorePostQuery()],
        get_query_operators=[GeneralStoreGetQuery()],
        enable_default_search=True,
        include_in_schema=False,
        calculate_submission_id=True,
    )

    return resource
