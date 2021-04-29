from mp_api.core.resource import GetResource
from mp_api.routes.thermo.models import ThermoDoc

from mp_api.core.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
    VersionQuery,
)
from mp_api.routes.thermo.query_operators import (
    ThermoChemicalQuery,
    ThermoEnergyQuery,
    IsStableQuery,
)

from mp_api.routes.materials.query_operators import MultiMaterialIDQuery


def thermo_resource(thermo_store):
    resource = GetResource(
        thermo_store,
        ThermoDoc,
        query_operators=[
            VersionQuery(),
            MultiMaterialIDQuery(),
            ThermoChemicalQuery(),
            IsStableQuery(),
            ThermoEnergyQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ThermoDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Thermo"],
    )

    return resource
