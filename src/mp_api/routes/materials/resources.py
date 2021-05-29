from re import sub
from fastapi import HTTPException

from maggma.api.resource.read_resource import ReadOnlyResource
from maggma.api.resource.post_resource import PostOnlyResource


from emmet.core.material import MaterialsDoc
from mp_api.routes.materials.models.doc import FindStructure

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
)

from pymatgen.core import Composition
from pymongo import MongoClient  # type: ignore
from itertools import permutations
from fastapi import Query, Body


def materials_resource(materials_store, formula_autocomplete_store):
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

    def custom_autocomplete_prep(self):
        async def formula_autocomplete(
            text: str = Query(
                ..., description="Text to run against formula autocomplete",
            ),
            limit: int = Query(
                10, description="Maximum number of matches to show. Defaults to 10",
            ),
        ):
            store = formula_autocomplete_store

            try:

                comp = Composition(text)

                ind_str = []
                eles = []

                if len(comp) == 1:
                    d = comp.get_integer_formula_and_factor()

                    s = d[0] + str(int(d[1])) if d[1] != 1 else d[0]

                    ind_str.append(s)
                    eles.append(d[0])
                else:

                    comp_red = comp.reduced_composition.items()

                    for (i, j) in comp_red:

                        if j != 1:
                            ind_str.append(i.name + str(int(j)))
                        else:
                            ind_str.append(i.name)

                        eles.append(i.name)

                final_terms = ["".join(entry) for entry in permutations(ind_str)]

                pipeline = [
                    {
                        "$search": {
                            "index": "formula_autocomplete",
                            "text": {"path": "formula_pretty", "query": final_terms},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "formula_pretty": 1,
                            "elements": 1,
                            "length": {"$strLenCP": "$formula_pretty"},
                        }
                    },
                    {
                        "$match": {
                            "length": {"$gte": len(final_terms[0])},
                            "elements": {"$all": eles},
                        }
                    },
                    {"$limit": limit},
                    {"$sort": {"length": 1}},
                    {"$project": {"elements": 0, "length": 0}},
                ]

                store.connect()

                data = list(store._collection.aggregate(pipeline, allowDiskUse=True))

                response = {"data": data}

            except Exception:
                raise HTTPException(
                    status_code=404,
                    detail="Cannot autocomplete with provided formula.",
                )

            return response

        self.router.get(
            "/formula_autocomplete/",
            response_model_exclude_unset=True,
            response_description="Get autocomplete results for a formula",
            tags=self.tags,
        )(formula_autocomplete)

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
        custom_endpoint_funcs=[custom_version_prep, custom_autocomplete_prep],
    )

    return resource


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
