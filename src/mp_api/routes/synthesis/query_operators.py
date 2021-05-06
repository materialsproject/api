import re
from collections import defaultdict
from typing import Optional, List, Dict

from fastapi import Query
from pymatgen.core import Composition

from mp_api.core.query_operator import STORE_PARAMS, QueryOperator


class SynthesisTypeQuery(QueryOperator):
    """
    Method to query the database for a specific synthesis type.
    """

    def query(
            self,
            synthesis_type: Optional[List[str]] = Query(
                None, description="Type of synthesis to include.",
                regex="solid-state|sol-gel"
            ),
    ) -> STORE_PARAMS:
        crit = defaultdict(dict)  # type: dict
        if synthesis_type:
            crit["synthesis_type"] = {
                '$in': synthesis_type
            }

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("synthesis_type", False)]


class SynthesisTargetFormulaQuery(QueryOperator):
    """
    Method to generate a query for synthesis data using a target material chemical formula
    """

    def query(
            self,
            target_formula: Optional[str] = Query(
                None, description="Chemical formula of the target material.",
            ),
    ) -> STORE_PARAMS:
        crit = defaultdict(dict)  # type: dict
        if target_formula:
            reduced_formula = Composition(target_formula).get_reduced_formula_and_factor()[0]
            crit["targets_formula_s"] = reduced_formula

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("targets_formula_s", False)]


class SynthesisPrecursorFormulaQuery(QueryOperator):
    """
    Method to generate a query for synthesis data using a precursor material chemical formula
    """

    def query(
            self,
            precursor_formula: Optional[str] = Query(
                None, description="Chemical formula of the precursor material.",
            ),
    ) -> STORE_PARAMS:
        crit = defaultdict(dict)  # type: dict

        if precursor_formula:
            reduced_formula = Composition(precursor_formula).get_reduced_formula_and_factor()[0]
            crit["precursors_formula_s"] = reduced_formula

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("precursors_formula_s", False)]


class TextSearchQuery(QueryOperator):
    """
    Method to search paragraph string for specific keywords.
    It also hides paragraph characters beyond 100 to make results compliant with publisher agreements.
    """

    def query(
            self,
            keywords: Optional[str] = Query(
                None, description="Comma delimited string keywords to search synthesis paragraph with.",
            ),
    ):
        crit = defaultdict(dict)  # type: dict

        if keywords:
            crit["$text"] = {
                "$search": keywords
            }

        return {"criteria": crit}

    def hide_chars(self, doc, limit=100):
        # If the text was not present, return immediately.
        if not isinstance(doc.get("paragraph_string", None), str):
            return doc

        if len(doc["paragraph_string"]) > limit:
            text = doc["paragraph_string"][:limit]

            # Make results nicer by cutting incomplete words of max 15 characters.
            # For example: "This is an incomplete sente" becomes "This is an incomplete "
            trailing = re.search(r"(?<![\w\d])[\w\d]{,15}$", text)
            if trailing is not None:
                text = text[:trailing.start()]

            text += "..."

            doc["paragraph_string"] = text

        return doc

    def post_process(self, docs: List[Dict]) -> List[Dict]:
        for doc in docs:
            self.hide_chars(doc)

        return docs


class ExperimentOperationsQuery(QueryOperator):
    """
    Method to query for syntheses with specific operations.
    """

    def query(
            self,
            operations: Optional[List[str]] = Query(
                None, description="List of operations that syntheses must have.",
                regex="StartingSynthesis|MixingOperation|ShapingOperation|DryingOperation|HeatingOperation|QuenchingOperation",
            ),
    ) -> STORE_PARAMS:
        crit = defaultdict(dict)  # type: dict
        if operations:
            crit["operations.type"] = {
                '$all': operations
            }

        return {"criteria": crit}

    def ensure_indexes(self):
        return [("operations.type", False)]
