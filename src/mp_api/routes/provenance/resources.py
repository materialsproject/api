from maggma.api.resource import ReadOnlyResource
from maggma.api.query_operator import PaginationQuery

from emmet.core.provenance import ProvenanceDoc


def provenance_resource(provenance_store):
    resource = ReadOnlyResource(
        provenance_store,
        ProvenanceDoc,
        query_operators=[PaginationQuery()],
        tags=["Provenance"],
        disable_validation=True,
        enable_default_search=False,
    )

    return resource
