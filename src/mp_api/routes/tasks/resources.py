from maggma.api.resource import ReadOnlyResource
from mp_api.routes.tasks.models import DeprecationDoc, TaskDoc, TrajectoryDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.tasks.query_operators import (
    MultipleTaskIDsQuery,
    TrajectoryQuery,
    DeprecationQuery,
)
from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
)


def task_resource(task_store):
    resource = ReadOnlyResource(
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
    resource = ReadOnlyResource(
        materials_store,
        DeprecationDoc,
        query_operators=[DeprecationQuery(), PaginationQuery()],
        tags=["Tasks"],
        enable_get_by_key=False,
        enable_default_search=True,
        sub_path="/deprecation/",
    )

    return resource


def trajectory_resource(task_store):
    resource = ReadOnlyResource(
        task_store,
        TrajectoryDoc,
        query_operators=[TrajectoryQuery(), PaginationQuery()],
        key_fields=["task_id", "calcs_reversed"],
        tags=["Tasks"],
        sub_path="/trajectory/",
    )

    return resource
