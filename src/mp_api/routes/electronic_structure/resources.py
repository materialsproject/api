from maggma.api.query_operator.dynamic import NumericQuery
from maggma.api.resource import ReadOnlyResource
from emmet.core.electronic_structure import ElectronicStructureDoc

from fastapi import HTTPException
from fastapi.param_functions import Path, Query

from mp_api.core.utils import api_sanitize
from mp_api.core.models import Response
from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery

from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
)

from mp_api.routes.electronic_structure.query_operators import (
    ESSummaryDataQuery,
    BSDataQuery,
    DOSDataQuery,
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
    )

    return resource


def bs_resource(es_store, s3_store):
    def custom_bs_endpoint_prep(self):

        self.s3 = s3_store
        model = api_sanitize(BSObjectDoc, allow_dict_msonable=True)
        model_name = model.__name__
        key_name = "task_id"

        async def get_object(
            task_id: str = Query(
                ..., alias=key_name, title=f"The {key_name} of the {model_name} to get",
            ),
        ):
            f"""
            Get's a document by the primary key in the store

            Args:
                {key_name}: the calculation id of a single {model_name}

            Returns:
                a single {model_name} document
            """

            self.s3.connect()

            bs_object_doc = None

            try:
                bs_object_doc = self.s3.query_one({"task_id": task_id})

                if not bs_object_doc:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Band structure with task_id = {task_id} not found",
                    )

            except ValueError:
                raise HTTPException(
                    status_code=404,
                    detail=f"Band structure with task_id = {task_id} not found",
                )

            return {"data": [bs_object_doc]}

        self.router.get(
            "/object/",
            response_description=f"Get an {model_name} by {key_name}",
            response_model=Response[model],
            response_model_exclude_unset=True,
            tags=self.tags,
        )(get_object)

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
        custom_endpoint_funcs=[custom_bs_endpoint_prep],
    )

    return resource


def dos_resource(es_store, s3_store):
    def custom_dos_endpoint_prep(self):

        self.s3 = s3_store
        model = api_sanitize(DOSObjectDoc, allow_dict_msonable=True)
        model_name = model.__name__
        key_name = "task_id"

        async def get_object(
            task_id: str = Query(
                ..., alias=key_name, title=f"The {key_name} of the {model_name} to get",
            ),
        ):
            f"""
            Get's a document by the primary key in the store

            Args:
                {key_name}: the calculation id of a single {model_name}

            Returns:
                a single {model_name} document
            """

            self.s3.connect()

            dos_object_doc = None

            try:
                dos_object_doc = self.s3.query_one({"task_id": task_id})

                if not dos_object_doc:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Density of states with task_id = {task_id} not found",
                    )

            except ValueError:
                raise HTTPException(
                    status_code=404,
                    detail=f"Density of states with task_id = {task_id} not found",
                )

            return {"data": [dos_object_doc]}

        self.router.get(
            "/object/",
            response_description=f"Get an {model_name} by {key_name}",
            response_model=Response[model],
            response_model_exclude_unset=True,
            tags=self.tags,
        )(get_object)

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
        custom_endpoint_funcs=[custom_dos_endpoint_prep],
        enable_get_by_key=False,
    )

    return resource
