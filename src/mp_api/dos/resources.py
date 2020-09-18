from mp_api.core.resource import Resource
from mp_api.dos.models.doc import DOSDoc, DOSObjectReturn

from fastapi.param_functions import Query

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery, MinMaxQuery

from mp_api.core.utils import STORE_PARAMS
from fastapi import Path, HTTPException, Depends


def dos_resource(dos_store, s3_store):
    def custom_dos_endpoint_prep(self):
        key_name = self.store.key
        model_name = self.model.__name__

        field_input = SparseFieldsQuery(
            self.model, [self.store.key, self.store.last_updated_field]
        ).query

        async def get_by_key(
            key: str = Path(
                ..., alias=key_name, title=f"The {key_name} of the {model_name} to get",
            ),
            fields: STORE_PARAMS = Depends(field_input),
            return_dos_object: bool = Query(
                False,
                description="Whether to return the density of states object for a given material.",
            ),
        ):
            f"""
                    Get's a document by the primary key in the store

                    Args:
                        {key_name}: the id of a single {model_name}

                    Returns:
                        a single {model_name} document
                    """
            self.store.connect()

            if return_dos_object:

                self.response_model = DOSObjectReturn

                self.s3.connect()

                dos_entry = self.store.query_one(
                    criteria={self.store.key: key}, properties=["total.task_id"]
                )

                dos_task = dos_entry.get("task_id", None)

                if dos_task is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Band structure with {self.store.key} = {key} and {path_type} \
                            path type not found",
                    )

                item = self.s3.query_one({"task_id": dos_task})

            else:

                item = self.store.query_one(
                    criteria={self.store.key: key}, properties=fields["properties"]
                )

                if item is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item with {self.store.key} = {key} not found",
                    )

            response = {"data": [item]}

            return response

        self.router.get(
            f"/{{{key_name}}}/",
            response_description=f"Get an {model_name} by {key_name}",
            response_model=self.response_model,
            response_model_exclude_unset=True,
            tags=self.tags,
        )(get_by_key)

    # Define resource
    resource = Resource(
        dos_store,
        DOSDoc,
        query_operators=[
            FormulaQuery(),
            MinMaxQuery(),
            PaginationQuery(),
            SparseFieldsQuery(DOSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        custom_endpoint_funcs=[custom_dos_endpoint_prep],
        enable_get_by_key=False,
    )

    return resource

