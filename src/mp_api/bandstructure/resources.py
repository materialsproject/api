from fastapi.param_functions import Query
from mp_api.core.resource import Resource
from mp_api.bandstructure.models.doc import BSDoc, BSObjectReturn
from mp_api.bandstructure.models.core import BSPathType

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery, SortQuery
from mp_api.materials.query_operators import FormulaQuery, MinMaxQuery
from mp_api.bandstructure.query_operators import BSDataQuery

from mp_api.core.utils import STORE_PARAMS
from fastapi import HTTPException, Depends


def bs_resource(bs_store, s3_store):
    def custom_bs_endpoint_prep(self):

        self.s3 = s3_store
        model = BSObjectReturn
        model_name = model.__name__
        key_name = self.s3.key

        field_input = SparseFieldsQuery(
            model, [self.s3.key, self.s3.last_updated_field]
        ).query

        async def get_object(
            key: str = Query(
                ...,
                alias=key_name,
                title=f"The {key_name} of the {model_name} to get",
            ),
            path_type: BSPathType = Query(
                ...,
                title="The k-path convention type for the band structure object",
            ),
            fields: STORE_PARAMS = Depends(field_input),
        ):
            f"""
            Get's a document by the primary key in the store

            Args:
                {key_name}: the id of a single {model_name}

            Returns:
                a single {model_name} document
            """

            self.store.connect()

            self.s3.connect()

            bs_entry = self.store.query_one(
                criteria={self.store.key: key},
                properties=[f"{str(path_type.name)}.task_id"],
            )

            bs_task = bs_entry.get(str(path_type.name)).get("task_id", None)

            if bs_task is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Band structure with {self.store.key} = {key} not found",
                )

            item = self.s3.query_one(
                {"task_id": bs_task}, properties=fields["properties"]
            )
            response = item

            return response

        self.router.get(
            "/object/",
            response_description=f"Get an {model_name} by {key_name}",
            response_model=model,
            response_model_exclude_unset=False,
            tags=self.tags,
        )(get_object)

    resource = Resource(
        bs_store,
        BSDoc,
        query_operators=[
            BSDataQuery(),
            FormulaQuery(),
            MinMaxQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(BSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        custom_endpoint_funcs=[custom_bs_endpoint_prep],
    )

    return resource
