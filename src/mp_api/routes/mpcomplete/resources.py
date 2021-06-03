from maggma.api.resource import SubmissionResource
from maggma.api.query_operator import PaginationQuery
from mp_api.routes.mpcomplete.models import MPCompleteDoc, MPCompleteDataStatus
from mp_api.routes.mpcomplete.query_operator import (
    MPCompletePostQuery,
    MPCompleteGetQuery,
)


def mpcomplete_resource(mpcomplete_store):
    resource = SubmissionResource(
        mpcomplete_store,
        MPCompleteDoc,
        post_query_operators=[MPCompletePostQuery()],
        get_query_operators=[MPCompleteGetQuery(), PaginationQuery()],
        tags=["MPComplete"],
        state_enum=MPCompleteDataStatus,
        default_state=MPCompleteDataStatus.submitted.value,
        calculate_submission_id=True,
        include_in_schema=True,
    )

    return resource
