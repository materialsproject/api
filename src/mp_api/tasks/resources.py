from mp_api.core.resource import GetResource
from mp_api.tasks.models import DeprecationDoc, TaskDoc, TrajectoryDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.tasks.query_operators import (
    MultipleTaskIDsQuery,
    TrajectoryQuery,
    DeprecationQuery,
)
from mp_api.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
)


def task_resource(task_store):
    resource = GetResource(
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
    resource = GetResource(
        materials_store,
        DeprecationDoc,
        query_operators=[DeprecationQuery(), PaginationQuery()],
        tags=["Tasks"],
        enable_get_by_key=False,
        enable_default_search=True,
    )

    return resource


def trajectory_resource(task_store):
    resource = GetResource(
        task_store,
        TrajectoryDoc,
        query_operators=[TrajectoryQuery(), PaginationQuery()],
        key_fields=["task_id", "calcs_reversed"],
        tags=["Tasks"],
    )

    return resource
