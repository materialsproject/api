from maggma.api.query_operator.dynamic import NumericQuery
from maggma.api.resource import ReadOnlyResource
from emmet.core.electronic_structure import ElectronicStructureDoc
from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery

from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
)

from mp_api.routes.electronic_structure.query_operators import (
    ESSummaryDataQuery,
    BSDataQuery,
    DOSDataQuery,
    ObjectQuery,
)
from mp_api.routes.electronic_structure.models.doc import BSObjectDoc, DOSObjectDoc


def es_resource(es_store):
    resource = ReadOnlyResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
            ESSummaryDataQuery(),
            FormulaQuery(),
            ElementsQuery(),
            NumericQuery(model=ElectronicStructureDoc),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ElectronicStructureDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Electronic Structure"],
        monty_encoded_response=True,
    )

    return resource


def bs_resource(es_store):
    resource = ReadOnlyResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
            BSDataQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ElectronicStructureDoc,
                default_fields=["material_id", "last_updated", "bandstructure"],
            ),
        ],
        tags=["Electronic Structure"],
        enable_get_by_key=False,
        sub_path="/bandstructure/",
        monty_encoded_response=True,
    )

    return resource


def bs_obj_resource(s3_store):
    resource = ReadOnlyResource(
        s3_store,
        BSObjectDoc,
        query_operators=[
            ObjectQuery(),
            SparseFieldsQuery(BSObjectDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        enable_get_by_key=False,
        enable_default_search=True,
        sub_path="/bandstructure/object/",
        monty_encoded_response=True,
    )
    return resource


def dos_resource(es_store):
    resource = ReadOnlyResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
            DOSDataQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ElectronicStructureDoc,
                default_fields=["material_id", "last_updated", "dos"],
            ),
        ],
        tags=["Electronic Structure"],
        enable_get_by_key=False,
        sub_path="/dos/",
        monty_encoded_response=True,
    )

    return resource


def dos_obj_resource(s3_store):
    resource = ReadOnlyResource(
        s3_store,
        DOSObjectDoc,
        query_operators=[
            ObjectQuery(),
            SparseFieldsQuery(DOSObjectDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        enable_get_by_key=False,
        enable_default_search=True,
        sub_path="/dos/object/",
        monty_encoded_response=True,
    )
    return resource
