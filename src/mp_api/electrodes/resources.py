from mp_api.core.resource import GetResource
from mp_api.electrodes.models import InsertionElectrodeDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.electrodes.query_operators import (
    VoltageStepQuery,
    InsertionVoltageStepQuery,
    InsertionElectrodeQuery,
    ElectrodeFormulaQuery,
)
from mp_api.materials.query_operators import ElementsQuery


def insertion_electrodes_resource(insertion_electrodes_store):
    resource = GetResource(
        insertion_electrodes_store,
        InsertionElectrodeDoc,
        query_operators=[
            ElectrodeFormulaQuery(),
            ElementsQuery(),
            VoltageStepQuery(),
            InsertionVoltageStepQuery(),
            InsertionElectrodeQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                InsertionElectrodeDoc, default_fields=["battery_id", "last_updated"],
            ),
        ],
        tags=["Electrodes"],
    )

    return resource
