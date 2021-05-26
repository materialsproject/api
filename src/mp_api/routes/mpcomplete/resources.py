from maggma.api.resource import UserSubmissionResource
from maggma.api.query_operator import PaginationQuery
from mp_api.routes.mpcomplete.models import MPCompleteDoc
from mp_api.routes.mpcomplete.query_operator import (
    MPCompletePostQuery,
    MPCompleteGetQuery,
)


def mpcomplete_resource(mpcomplete_store):
    resource = UserSubmissionResource(
        mpcomplete_store,
        MPCompleteDoc,
        post_query_operators=[MPCompletePostQuery()],
        get_query_operators=[MPCompleteGetQuery(), PaginationQuery()],
        tags=["MPComplete"],
        include_in_schema=True,
    )

    return resource
