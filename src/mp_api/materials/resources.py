from mp_api.core.resource import Resource
from mp_api.materials.models.doc import MaterialsCoreDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery, VersionQuery
from mp_api.materials.query_operators import (
    FormulaQuery,
    DeprecationQuery,
    MinMaxQuery,
    SymmetryQuery,
    MultiTaskIDQuery,
)

from pymongo import MongoClient  # type: ignore


def materials_resource(materials_store):
    def custom_endpoint_prep(self):
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

    resource = Resource(
        materials_store,
        MaterialsCoreDoc,
        query_operators=[
            VersionQuery(),
            FormulaQuery(),
            MultiTaskIDQuery(),
            SymmetryQuery(),
            DeprecationQuery(),
            MinMaxQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                MaterialsCoreDoc,
                default_fields=["task_id", "formula_pretty", "last_updated"],
            ),
        ],
        tags=["Materials"],
        custom_endpoint_funcs=[custom_endpoint_prep],
    )

    return resource
