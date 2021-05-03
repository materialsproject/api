from mp_api.core.resource import GetResource
from emmet.core.electronic_structure import ElectronicStructureDoc

from fastapi.param_functions import Query

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
    MinMaxQuery,
)

from mp_api.routes.electronic_structure.query_operators import (
    ESSummaryDataQuery,
    BSDataQuery,
    DOSDataQuery,
)


def es_resource(es_store):
    resource = GetResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
            ESSummaryDataQuery(),
            FormulaQuery(),
            ElementsQuery(),
            MinMaxQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ElectronicStructureDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Electronic Structure"],
    )

    return resource


def bs_resource(es_store):
    resource = GetResource(
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
    )

    return resource


def dos_resource(es_store):
    resource = GetResource(
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
    )

    return resource
