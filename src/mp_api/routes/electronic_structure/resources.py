from mp_api.core.resource import GetResource
from emmet.core.electronic_structure import ElectronicStructureDoc

from fastapi.param_functions import Query

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
    MinMaxQuery,
)
from mp_api.routes.dos.query_operators import DOSDataQuery

from mp_api.core.utils import STORE_PARAMS
from fastapi import HTTPException, Depends


def es_resource(es_store):
    resource = GetResource(
        es_store,
        ElectronicStructureDoc,
        query_operators=[
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
