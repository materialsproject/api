from maggma.api.resource.read_resource import ReadOnlyResource
from maggma.api.resource.post_resource import PostOnlyResource
from maggma.api.resource.aggregation import AggregationResource


from emmet.core.material import MaterialsDoc
from mp_api.routes.materials.models.doc import FindStructure, FormulaAutocomplete

from maggma.api.query_operator import (
    PaginationQuery,
    SparseFieldsQuery,
    SortQuery,
    VersionQuery,
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
        path="/find_structure/",
    )

    return resource


def formula_autocomplete_resource(formula_autocomplete_store):
    resource = AggregationResource(
        formula_autocomplete_store,
        FormulaAutocomplete,
        pipeline_query_operator=FormulaAutoCompleteQuery(),
        tags=["Materials"],
        path="/formula_autocomplete/",
    )

    return resource


def materials_resource(materials_store):
    def custom_version_prep(self):
        model_name = self.model.__name__

        async def get_versions():
            f"""
            Obtains the database versions for the data in {model_name}

            Returns:
                A list of database versions one can use to query on
            """

            try:
                conn = MongoClient(self.store.host, self.store.port)
                db = conn[self.store.database]
                if self.core.username != "":
                    db.authenticate(self.username, self.password)

            except AttributeError:
                conn = MongoClient(self.store.uri)
                db = conn[self.store.database]

            col_names = db.list_collection_names()

            d = [
                name.replace("_", ".")[15:]
                for name in col_names
                if "materials" in name
                if name != "materials.core"
            ]

            response = {"data": d}

            return response

        self.router.get(
            "/versions/",
            response_model_exclude_unset=True,
            response_description=f"Get versions of {model_name}",
            tags=self.tags,
        )(get_versions)

    resource = ReadOnlyResource(
        materials_store,
        MaterialsDoc,
        query_operators=[
            VersionQuery(default_version=MAPISettings().db_version),
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
        custom_endpoint_funcs=[custom_version_prep],
    )

    return resource

