from mp_api.core.resource import Resource
from mp_api.tasks.models import TaskDoc
from mp_api.tasks.utils import calcs_reversed_to_trajectory

from mp_api.materials.models.doc import MaterialsCoreDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery

from monty.json import jsanitize
import json
from typing import Callable

from fastapi import Request, Response, Path
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


def task_deprecation_resource(materials_store):
    def custom_deprecation_prep(self):
        async def check_deprecation(
            task_id: str = Path(
                ...,
                alias="task_id",
                title="Task id to check for deprecation.",
            ),
        ):
            """
            Checks whether a task_id is deprecated.

            Returns:
                Dictionary containing deprecation information
            """

            crit = {"deprecated_tasks": task_id}

            self.store.connect()

            deprecation = {"deprecated": False, "deprecation_reason": None}

            for r in self.store.query(criteria=crit, properties=["deprecated_tasks"]):
                if r != {}:
                    deprecation = {"deprecated": True, "deprecation_reason": None}
                    break

            response = {"data": deprecation}

            return response

        self.router.get(
            "/{task_id}/",
            response_model_exclude_unset=True,
            response_description="Check deprecation of a specific task_id",
            tags=self.tags,
        )(check_deprecation)

    resource = Resource(
        materials_store,
        MaterialsCoreDoc,
        query_operators=[
            PaginationQuery(),
        ],
        tags=["Tasks"],
        custom_endpoint_funcs=[custom_deprecation_prep],
        enable_get_by_key=False,
        enable_default_search=False,
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
                        calcs_reversed_to_trajectory(entry["calcs_reversed"])
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
