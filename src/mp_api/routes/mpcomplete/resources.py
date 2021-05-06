from mp_api.core.resource import ConsumerPostResource
from mp_api.routes.mpcomplete.models import MPCompleteDoc
from mp_api.routes.mpcomplete.query_operator import MPCompletePostQuery


def mpcomplete_resource(mpcomplete_store):
    resource = ConsumerPostResource(
        mpcomplete_store,
        MPCompleteDoc,
        query_operators=[MPCompletePostQuery()],
        tags=["MPComplete"],
        include_in_schema=True,
    )

    return resource
