from fastapi.param_functions import Path
from maggma.api.resource import ReadOnlyResource
from mp_api.core.models import Response
from mp_api.routes.charge_density.models import ChgcarDataDoc
from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery, SortQuery
from mp_api.core.utils import STORE_PARAMS
from fastapi import HTTPException, Depends


def charge_density_resource(s3_store):
    def custom_charge_density_endpoint_prep(self):

        self.s3 = s3_store
        model = ChgcarDataDoc
        model_name = model.__name__
        key_name = "task_id"

        field_input = SparseFieldsQuery(model, [key_name, self.s3.last_updated_field]).query

        async def get_chgcar_data(
            material_id: str = Path(
                ..., alias=key_name, title=f"The Material ID ({key_name}) associated with the {model_name}",
            ),
            fields: STORE_PARAMS = Depends(field_input),
        ):
            f"""
            Get's a document by the primary key in the store

            Args:
                material_id: The Materials Project ID ({key_name}) of a single {model_name}

            Returns:
                a single {model_name} document
            """

            self.s3.connect()

            item = self.s3.query_one({key_name: material_id}, properties=fields["properties"])

            if item is None:
                raise HTTPException(
                    status_code=404, detail=f"Item with {key_name} = {material_id} not found",
                )
            else:
                return {"data": [item]}

        self.router.get(
            f"/{{{key_name}}}/",
            response_description=f"Get an {model_name} by {key_name}",
            response_model=Response[model],
            response_model_exclude_unset=True,
            tags=self.tags,
        )(get_chgcar_data)

    resource = ReadOnlyResource(
        s3_store,
        ChgcarDataDoc,
        query_operators=[
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(ChgcarDataDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Charge Density"],
        custom_endpoint_funcs=[custom_charge_density_endpoint_prep],
        enable_default_search=False,
        enable_get_by_key=False,
    )

    return resource
