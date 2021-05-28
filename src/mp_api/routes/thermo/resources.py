from maggma.api.query_operator.dynamic import NumericQuery
from maggma.api.resource import ReadOnlyResource
from emmet.core.thermo import ThermoDoc

from maggma.api.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
    VersionQuery,
)
from mp_api.routes.thermo.query_operators import (
    ThermoChemicalQuery,
    IsStableQuery,
)

from mp_api.core.settings import MAPISettings

from mp_api.routes.materials.query_operators import MultiMaterialIDQuery


def thermo_resource(thermo_store):
    resource = ReadOnlyResource(
        thermo_store,
        ThermoDoc,
        query_operators=[
            VersionQuery(default_version=MAPISettings().db_version),
            MultiMaterialIDQuery(),
            ThermoChemicalQuery(),
            IsStableQuery(),
            NumericQuery(model=ThermoDoc),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ThermoDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Thermo"],
    )

    return resource
