from fastapi import HTTPException, Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS


class RoboTextSearchQuery(QueryOperator):
    """
    Method to generate a robocrystallographer text search query
    """

    def query(
        self,
        keywords: str = Query(
            ...,
            description="Comma delimited string keywords to search robocrystallographer description text with",
        ),
        skip: int = Query(0, description="Number of entries to skip in the search"),
        limit: int = Query(
            100,
            description="Max number of entries to return in a single query. Limited to 100",
        ),
    ) -> STORE_PARAMS:

        if not keywords.strip():
            raise HTTPException(
                status_code=400, detail="Must provide search keywords.",
            )

        pipeline = [
            {
                "$search": {
                    "index": "description",
                    "regex": {
                        "query": [word.strip() for word in keywords.split(",") if word],
                        "path": "description",
                        "allowAnalyzedField": True,
                    },
                }
            },
            {
                "$facet": {
                    "total_doc": [{"$count": "count"}],
                    "results": [
                        {
                            "$project": {
                                "_id": 0,
                                "task_id": 1,
                                "description": 1,
                                "condensed_structure": 1,
                                "last_updates": 1,
                                "search_score": {"$meta": "searchScore"},
                            }
                        }
                    ],
                }
            },
            {"$unwind": "$results"},
            {"$unwind": "$total_doc"},
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": ["$results", {"total_doc": "$total_doc.count"}]
                    }
                }
            },
            {"$sort": {"search_score": -1}},
            {"$skip": skip},
            {"$limit": limit},
        ]
        return {"pipeline": pipeline}

    def post_process(self, docs):
        self.total_doc = docs[0]["total_doc"]
        return docs

    def meta(self):
        return {"total_doc": self.total_doc}

    def ensure_indexes(self):  # pragma: no cover
        return [("description", False)]
