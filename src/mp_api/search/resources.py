from mp_api.core.resource import Resource
from mp_api.search.models import SearchDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.materials.query_operators import (
    FormulaQuery,
    MinMaxQuery,
    SymmetryQuery,
    DeprecationQuery,
)

from mp_api.surface_properties.query_operators import SurfaceMinMaxQuery
from mp_api.search.query_operators import (
    SearchBandGapQuery,
    HasPropsQuery,
    ThermoEnergySearchQuery,
    SearchTaskIDsQuery,
    SearchIsStableQuery,
    SearchElasticityQuery,
    SearchMagneticQuery,
    SearchDielectricPiezoQuery
)


def search_resource(eos_store):
    resource = Resource(
        eos_store,
        SearchDoc,
        query_operators=[
            SearchTaskIDsQuery(),
            FormulaQuery(),
            MinMaxQuery(),
            SymmetryQuery(),
            ThermoEnergySearchQuery(),
            SearchIsStableQuery(),
            SearchBandGapQuery(),
            SearchElasticityQuery(),
            SearchDielectricPiezoQuery(),
            SurfaceMinMaxQuery(),
            SearchMagneticQuery(),
            HasPropsQuery(),
            DeprecationQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SearchDoc, default_fields=["task_id"]),
        ],
        tags=["Search"],
    )

    return resource
