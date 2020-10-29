import io
from fastapi.param_functions import Path
from fastapi.responses import StreamingResponse

from mp_api.core.resource import Resource
from mp_api.phonon.models import PhononBSDoc, PhononImgDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery


def phonon_bs_resource(phonon_bs_store):
    resource = Resource(
        phonon_bs_store,
        PhononBSDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(PhononBSDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Phonon"],
        enable_default_search=False,
    )

    return resource


def phonon_img_resource(phonon_img_store):
    def phonon_img_prep(self):
        async def get_image(
            task_id: str = Path(
                ...,
                alias="task_id",
                title="Materials Project ID of the material.",
            ),
        ):
            """
            Obtains a phonon band structure image if available.

            Returns:
                Phonon band structure image.
            """

            crit = {"task_id": task_id}

            self.store.connect()

            img = self.store.query_one(criteria=crit, properties=["plot"])["plot"]

            response = StreamingResponse(
                io.BytesIO(img),
                media_type="img/png",
                headers={
                    "Content-Disposition": 'inline; filename="{}_phonon_bs.png"'.format(
                        task_id
                    )
                },
            )

            return response

        self.router.get(
            "/{task_id}/",
            response_model_exclude_unset=True,
            response_description="Get phonon band structure image.",
            tags=self.tags,
        )(get_image)

    resource = Resource(
        phonon_img_store,
        PhononImgDoc,
        # query_operators=[PaginationQuery()],
        tags=["Phonon"],
        custom_endpoint_funcs=[phonon_img_prep],
        enable_default_search=False,
        enable_get_by_key=False,
    )

    return resource
