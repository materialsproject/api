from fastapi.param_functions import Query
from mp_api.core.resource import Resource
from mp_api.tasks.models import TaskDoc
from mp_api.tasks.utils import calcs_reversed_to_trajectory

from mp_api.materials.models.doc import MaterialsCoreDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.tasks.query_operators import MultipleTaskIDsQuery
from mp_api.materials.query_operators import ElementsQuery, FormulaQuery


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
            ElementsQuery(),
            MultipleTaskIDsQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                TaskDoc, default_fields=["task_id", "formula_pretty", "last_updated"],
            ),
        ],
        tags=["Tasks"],
    )

    return resource


def task_deprecation_resource(materials_store):
    def custom_deprecation_prep(self):
        async def check_deprecation(
            task_ids: str = Query(
                ...,
                alias="task_ids",
                title="Comma separated list of task ids to check for deprecation.",
                description="Comma separated list of task ids to check for deprecation.",
            ),
        ):
            """
            Checks whether a list of task_ids is deprecated.

            Returns:
                Dictionary containing deprecation information
            """

            tlist = task_ids.split(",")

            crit = {"deprecated_tasks": {"$in": tlist}}

            self.store.connect()

            deprecation = {
                task_id: {"deprecated": False, "deprecation_reason": None}
                for task_id in tlist
            }

            q = self.store.query(
                criteria=crit, properties=["deprecated_tasks", "task_id"]
            )

            for r in q:

                deprecation[r["task_id"]] = {
                    "deprecated": True,
                    "deprecation_reason": None,
                }

            response = {"data": deprecation}

            return response

        self.router.get(
            "/",
            response_model_exclude_unset=True,
            response_description="Check deprecation of a list of task_ids",
            tags=self.tags,
        )(check_deprecation)

    resource = Resource(
        materials_store,
        MaterialsCoreDoc,
        query_operators=[PaginationQuery()],
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

                d = json.loads(response.body)

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
