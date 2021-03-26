from fastapi import Query
from mp_api.core.resource import GetResource
from mp_api.robocrys.models import RobocrysDoc


def robo_resource(robo_store):
    def custom_robo_prep(self):
        async def query_robo_text(
            keywords: str = Query(
                ...,
                description="Comma delimited string keywords to search robocrystallographer description text with",
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
                        "index": "description",
                        "regex": {
                            "query": [word + ".*" for word in keywords.split(",")],
                            "path": "description",
                            "allowAnalyzedField": True,
                        },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "task_id": 1,
                        "description": 1,
                        "condensed_structure": 1,
                        "last_updates": 1,
                        "search_score": {"$meta": "searchScore"},
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
            response_description="Find robocrystallographer documents through text search.",
            tags=self.tags,
        )(query_robo_text)

    resource = GetResource(
        robo_store,
        RobocrysDoc,
        tags=["Robocrystallographer"],
        custom_endpoint_funcs=[custom_robo_prep],
        enable_default_search=False,
    )

    return resource
