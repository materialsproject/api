from fastapi.param_functions import Query
from mp_api.core.resource import Resource
from mp_api.bandstructure.models.doc import BSDoc, BSObjectReturn
from mp_api.bandstructure.models.core import BSPathType

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery, MinMaxQuery
from mp_api.bandstructure.query_operators import BSDataQuery

from mp_api.core.utils import STORE_PARAMS
from fastapi import Path, HTTPException, Depends


def bs_resource(bs_store, s3_store):
    def custom_bs_endpoint_prep(self):
        key_name = self.store.key
        model_name = self.model.__name__

        self.s3 = s3_store

        field_input = SparseFieldsQuery(
            self.model, [self.store.key, self.store.last_updated_field]
        ).query

        async def get_by_key(
            key: str = Path(
                ..., alias=key_name, title=f"The {key_name} of the {model_name} to get",
            ),
            fields: STORE_PARAMS = Depends(field_input),
            return_bandstructure_object: bool = Query(
                False,
                description="Whether to return the band structure object and its \
                metadata for a given material. Path type must also be specified.",
            ),
            path_type: BSPathType = Query(
                None,
                description="Band structure k-path type if the object is to be returned.",
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

            if return_bandstructure_object:

                self.response_model = BSObjectReturn

                if path_type is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Must specify path type to retrieve a band structure object.",
                    )

                self.s3.connect()

                bs_entry = self.store.query_one(
                    criteria={self.store.key: key}, properties=[f"{path_type}.task_id"]
                )

                bs_task = bs_entry.get(path_type).get("task_id", None)

                if bs_task is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Band structure with {self.store.key} = {key} and {path_type} \
                            path type not found",
                    )

                item = self.s3.query_one({"task_id": bs_task})

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

    resource = Resource(
        bs_store,
        BSDoc,
        query_operators=[
            BSDataQuery(),
            FormulaQuery(),
            MinMaxQuery(),
            PaginationQuery(),
            SparseFieldsQuery(BSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        custom_endpoint_funcs=[custom_bs_endpoint_prep],
        enable_get_by_key=False,
    )

    return resource

