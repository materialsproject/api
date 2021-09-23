from maggma.api.query_operator.dynamic import NumericQuery
from maggma.api.resource import ReadOnlyResource
from emmet.core.electronic_structure import ElectronicStructureDoc
from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery

from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
    DeprecationQuery,
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
            DeprecationQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ElectronicStructureDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Electronic Structure"],
        disable_validation=True,
    )

    return resource


def bs_resource(es_store):
    resource = ReadOnlyResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
            BSDataQuery(),
            DeprecationQuery(),
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
        disable_validation=True,
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
        disable_validation=True,
    )
    return resource


def dos_resource(es_store):
    resource = ReadOnlyResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
            DOSDataQuery(),
            DeprecationQuery(),
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
        disable_validation=True,
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
        disable_validation=True,
    )
    return resource
