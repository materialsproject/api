from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from pymatgen.core import Composition
from fastapi import HTTPException

from collections import defaultdict


class SynthFormulaQuery(QueryOperator):
    """
    Method to generate a query for synthesis data using a chemical formula
    """

    def query(
        self,
        formula: Optional[str] = Query(
            None, description="Chemical formula of the material.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if formula:

            reduced_formula = Composition(formula).get_reduced_formula_and_factor()[0]
            crit["formula"] = reduced_formula

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("formula", False)]


class SynthesisTextSearchQuery(QueryOperator):
    """
    Method to generate a synthesis text search query
    """

    def query(
        self,
        keywords: str = Query(
            ...,
            description="Comma delimited string keywords to search synthesis description text with",
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
                    "index": "synth_descriptions",
                    "text": {
                        "query": [word.strip() for word in keywords.split(",") if word],
                        "path": "text",
                    },
                    "highlight": {"path": "text", "maxNumPassages": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "doi": 1,
                    "formula": 1,
                    "text": 1,
                    "search_score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"},
                }
            },
            {"$sort": {"search_score": -1}},
            {"$skip": skip},
            {"$limit": limit},
        ]

        return {"pipeline": pipeline}

    def ensure_indexes(self):
        return [("text", False)]
