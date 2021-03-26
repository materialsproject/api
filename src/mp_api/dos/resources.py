from mp_api.core.resource import GetResource
from mp_api.dos.models.doc import DOSDoc, DOSObjectReturn

from fastapi.param_functions import Query

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.materials.query_operators import ElementsQuery, FormulaQuery, MinMaxQuery
from mp_api.dos.query_operators import DOSDataQuery

from mp_api.core.utils import STORE_PARAMS
from fastapi import HTTPException, Depends


def dos_resource(dos_store, s3_store):
    def custom_dos_endpoint_prep(self):

        self.s3 = s3_store
        model = DOSObjectReturn
        model_name = model.__name__
        key_name = self.s3.key

        field_input = SparseFieldsQuery(
            model, [self.s3.key, self.s3.last_updated_field]
        ).query

        async def get_object(
            key: str = Query(
                ..., alias=key_name, title=f"The {key_name} of the {model_name} to get",
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

            dos_entry = self.store.query_one(
                criteria={self.store.key: key}, properties=["total.task_id"]
            )

            dos_task = dos_entry.get("total", None).get("task_id", None)

            if dos_task is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"DOS with {self.store.key} = {key} not found",
                )

            item = self.s3.query_one(
                {"task_id": dos_task}, properties=fields["properties"]
            )
            response = item

            return response

        self.router.get(
            "/object/",
            response_description=f"Get an {model_name} by {key_name}",
            response_model=model,
            response_model_exclude_unset=True,
            tags=self.tags,
        )(get_object)

    # Define resource
    resource = GetResource(
        dos_store,
        DOSDoc,
        query_operators=[
            DOSDataQuery(),
            FormulaQuery(),
            ElementsQuery(),
            MinMaxQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(DOSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        custom_endpoint_funcs=[custom_dos_endpoint_prep],
    )

    return resource
