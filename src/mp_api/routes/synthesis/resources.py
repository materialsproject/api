from mp_api.core.resource import GetResource
from mp_api.routes.synthesis.models import SynthesisDoc

from mp_api.routes.synthesis.query_operators import SynthFormulaQuery
from mp_api.core.query_operator import SortQuery, PaginationQuery, SparseFieldsQuery

from fastapi import Query


def synth_resource(synth_store):
    def custom_synth_prep(self):
        async def query_synth_text(
            keywords: str = Query(
                ...,
                description="Comma delimited string keywords to search synthesis description text with",
            ),
            skip: int = Query(0, description="Number of entries to skip in the search"),
            limit: int = Query(
                100,
                description="Max number of entries to return in a single query. Limited to 100",
            ),
        ):

            pipeline = [
                {
                    "$search": {
                        "index": "synth_descriptions",
                        "regex": {
                            # TODO: should handle multiple-word queries explicitly, for now will split by
                            # space and query as multiple words
                            "query": [word + ".*" for word in keywords.replace(" ", ",").split(",") if word],
                            "path": "text",
                            "allowAnalyzedField": True,
                        },
                        "highlight": {
                            "path": "text",
                            "maxNumPassages": 1
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "doi": 1,
                        "formula": 1,
                        "text": 1,
                        "search_score": {"$meta": "searchScore"},
                        "highlights": {"$meta": "searchHighlights"}
                    }
                },
                {"$sort": {"search_score": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

            self.store.connect()

            data = list(self.store._collection.aggregate(pipeline, allowDiskUse=True))

            response = {"data": data}

            return response

        self.router.get(
            "/text_search/",
            response_model=self.response_model,
            response_model_exclude_unset=True,
            response_description="Find synthesis description documents through text search.",
            tags=self.tags,
        )(query_synth_text)

    resource = GetResource(
        synth_store,
        SynthesisDoc,
        query_operators=[
            SynthFormulaQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SynthesisDoc, default_fields=["formula", "doi"]),
        ],
        tags=["Synthesis"],
        custom_endpoint_funcs=[custom_synth_prep],
        enable_default_search=True,
        enable_get_by_key=False,
    )

    return resource
