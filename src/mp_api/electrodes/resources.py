from mp_api.core.resource import Resource
from mp_api.electrodes.models import InsertionElectrodeDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.electrodes.query_operators import (
    VoltageStepQuery,
    InsertionVoltageStepQuery,
    InsertionElectrodeQuery,
)


def insertion_electrodes_resource(insertion_electrodes_store):
    resource = Resource(
        insertion_electrodes_store,
        InsertionElectrodeDoc,
        query_operators=[
            VoltageStepQuery(),
            InsertionVoltageStepQuery(),
            InsertionElectrodeQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                InsertionElectrodeDoc, default_fields=["task_id", "last_updated"],
            ),
        ],
        tags=["Electrodes"],
    )

    return resource
