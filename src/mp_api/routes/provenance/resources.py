from maggma.api.resource import ReadOnlyResource
from maggma.api.query_operator import PaginationQuery
from mp_api.routes.materials.query_operators import DeprecationQuery

from emmet.core.provenance import ProvenanceDoc


def provenance_resource(provenance_store):
    resource = ReadOnlyResource(
        provenance_store,
        ProvenanceDoc,
        query_operators=[DeprecationQuery(), PaginationQuery()],
        tags=["Provenance"],
        disable_validation=True,
        enable_default_search=False,
    )

    return resource
