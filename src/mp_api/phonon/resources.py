from mp_api.core.resource import Resource
from mp_api.phonon.models import PhononBSDoc, PhononImgDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery


def phonon_bs_resource(phonon_bs_store):
    resource = Resource(
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
    resource = Resource(
        phonon_img_store,
        PhononImgDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(PhononBSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Phonon"],
        enable_default_search=False,
    )

    return resource
