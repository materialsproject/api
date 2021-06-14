import io
from emmet.core.mpid import MPID

from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from fastapi import Path
from fastapi.responses import StreamingResponse


class PhononImgQuery(QueryOperator):
    """
    Method to generate a query on phonon image data.
    """

    def query(
        self,
        task_id: MPID = Path(
            ...,
            description="The calculation (task) ID associated with the data object",
        ),
    ) -> STORE_PARAMS:

        return {"criteria": {"task_id": str(task_id)}}
