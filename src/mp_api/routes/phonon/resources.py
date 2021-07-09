from maggma.api.resource import ReadOnlyResource
from mp_api.routes.phonon.models import PhononBSDOSDoc
from mp_api.routes.phonon.query_operators import PhononImgQuery

from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def phonon_bsdos_resource(phonon_bs_store):
    resource = ReadOnlyResource(
        phonon_bs_store,
        PhononBSDOSDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(
                PhononBSDOSDoc, default_fields=["task_id", "last_updated"]
            ),
        ],
        tags=["Phonon"],
        enable_default_search=False,
        disable_validation=True,
    )

    return resource
