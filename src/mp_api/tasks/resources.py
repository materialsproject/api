from mp_api.core.resource import Resource
from mp_api.tasks.models import TaskDoc
from mp_api.tasks.utils import calcs_revered_to_trajectory

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery

from monty.json import jsanitize
import json
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute


def task_resource(task_store):
    resource = Resource(
        task_store,
        TaskDoc,
        query_operators=[
            FormulaQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                TaskDoc,
                default_fields=["task_id", "formula_pretty", "last_updated"],
            ),
        ],
        tags=["Tasks"],
    )

    return resource


def trajectory_resource(task_store):
    class TrajectoryProcess(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()

            async def custom_route_handler(request: Request) -> Response:
                response: Response = await original_route_handler(request)

                d = json.loads(response.body, encoding=response.charset)

                trajectories = []
                for entry in d["data"]:
                    trajectories.append(
                        calcs_revered_to_trajectory(entry["calcs_reversed"])
                    )

                trajectories = jsanitize(trajectories)

                response.body = json.dumps(
                    trajectories,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=None,
                    separators=(",", ":"),
                ).encode(response.charset)

                traj_len = str(len(response.body))
                response.headers["content-length"] = traj_len

                return response

            return custom_route_handler

    resource = Resource(
        task_store,
        TaskDoc,
        query_operators=[FormulaQuery(), PaginationQuery()],
        route_class=TrajectoryProcess,
        key_fields=["calcs_reversed"],
        tags=["Tasks"],
    )

    return resource
