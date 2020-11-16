from mp_api.core.resource import Resource
from mp_api.thermo.models import ThermoDoc

from mp_api.core.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
    VersionQuery,
)
from mp_api.thermo.query_operators import (
    ThermoChemicalQuery,
    ThermoEnergyQuery,
    IsStableQuery,
)


def thermo_resource(thermo_store):
    resource = Resource(
        thermo_store,
        ThermoDoc,
        query_operators=[
            VersionQuery(),
            ThermoChemicalQuery(),
            IsStableQuery(),
            ThermoEnergyQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(ThermoDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Thermo"],
    )

    return resource
