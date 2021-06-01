from itertools import permutations
from fastapi import Body, HTTPException, Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from pymatgen.analysis.structure_matcher import ElementComparator, StructureMatcher
from pymatgen.core.composition import Composition, CompositionError
from pymatgen.core.structure import Structure


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
        return {"pipeline": pipeline}

    def ensure_indexes(self):
        return [("description", False)]
