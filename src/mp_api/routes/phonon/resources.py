from maggma.api.resource import ReadOnlyResource
from mp_api.routes.phonon.models import PhononBSDoc, PhononImgDoc
from mp_api.routes.phonon.query_operators import PhononImgQuery

from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def phonon_bs_resource(phonon_bs_store):
    resource = ReadOnlyResource(
        phonon_bs_store,
        PhononBSDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(PhononBSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Phonon"],
        enable_default_search=False,
    )

    return resource


def phonon_img_resource(phonon_img_store):

    resource = ReadOnlyResource(
        phonon_img_store,
        PhononImgDoc,
        tags=["Phonon"],
        enable_default_search=False,
        enable_get_by_key=True,
        key_fields=["plot", "task_id", "last_updated"],
        sub_path="/image/",
    )

    return resource
