from maggma.api.resource.read_resource import ReadOnlyResource
from maggma.api.resource.post_resource import PostOnlyResource
from maggma.api.resource.aggregation import AggregationResource


from emmet.core.material import MaterialsDoc
from mp_api.routes.materials.models.doc import FindStructure, FormulaAutocomplete

from maggma.api.query_operator import (
    PaginationQuery,
    SparseFieldsQuery,
    SortQuery,
    NumericQuery,
)

from mp_api.core.settings import MAPISettings

from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
    DeprecationQuery,
    SymmetryQuery,
    MultiTaskIDQuery,
    FindStructureQuery,
    FormulaAutoCompleteQuery,
)

from pymongo import MongoClient  # type: ignore


def find_structure_resource(materials_store):
    resource = PostOnlyResource(
        materials_store,
        FindStructure,
        key_fields=["structure", "task_id"],
        query_operators=[FindStructureQuery()],
        tags=["Materials"],
        sub_path="/find_structure/",
    )

    return resource


def formula_autocomplete_resource(formula_autocomplete_store):
    resource = AggregationResource(
        formula_autocomplete_store,
        FormulaAutocomplete,
        pipeline_query_operator=FormulaAutoCompleteQuery(),
        tags=["Materials"],
        sub_path="/formula_autocomplete/",
    )

    return resource


def materials_resource(materials_store):

    resource = ReadOnlyResource(
        materials_store,
        MaterialsDoc,
        query_operators=[
            FormulaQuery(),
            ElementsQuery(),
            MultiTaskIDQuery(),
            SymmetryQuery(),
            DeprecationQuery(),
            NumericQuery(model=MaterialsDoc),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                MaterialsDoc,
                default_fields=["material_id", "formula_pretty", "last_updated"],
            ),
        ],
        tags=["Materials"],
        disable_validation=True,
    )

    return resource
