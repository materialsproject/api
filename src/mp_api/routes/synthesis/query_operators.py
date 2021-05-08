import re
from collections import defaultdict
from typing import Optional, List, Dict

from fastapi import Query
from pymatgen.core import Composition

from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.routes.synthesis.models import SynthesisTypeEnum, OperationTypeEnum

__all__ = [
    'SynthesisTypeQuery',
    'SynthesisTargetFormulaQuery',
    'SynthesisPrecursorFormulaQuery',
    'TextSearchQuery',
    'ExperimentOperationsQuery',
    'ExperimentConditionsQuery',
]


class SynthesisTypeQuery(QueryOperator):
    """
    Method to query the database for a specific synthesis type.
    """

    def query(
            self,
            synthesis_type: Optional[List[SynthesisTypeEnum]] = Query(
                None, description="Type of synthesis to include.",
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

    def make_ellipsis(self, text, limit=100):
        if len(text) > limit:
            text = text[:limit]

            # Make results nicer by cutting incomplete words of max 15 characters.
            # For example: "This is an incomplete sente" becomes "This is an incomplete "
            trailing = re.search(r"(?<![\w\d])[\w\d]{,15}$", text)
            if trailing is not None:
                text = text[:trailing.start()]

            text += "..."

        return text

    def post_process(self, docs: List[Dict]) -> List[Dict]:
        for doc in docs:
            if isinstance(doc.get("paragraph_string", None), str):
                doc["paragraph_string"] = self.make_ellipsis(doc["paragraph_string"])

        return docs


class ExperimentOperationsQuery(QueryOperator):
    """
    Method to query for syntheses with specific operations.
    """

    def query(
            self,
            operations: Optional[List[OperationTypeEnum]] = Query(
                None, description="List of operations that syntheses must have.",
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


class ExperimentConditionsQuery(QueryOperator):
    """
    Method to query for syntheses with specific experimental conditions.
    """

    def query(
            self,
            condition_heating_temperature_above: Optional[float] = Query(
                None, description="Minimal heating temperature.",
            ),
            condition_heating_temperature_below: Optional[float] = Query(
                None, description="Maximal heating temperature.",
            ),
            condition_heating_time_above: Optional[float] = Query(
                None, description="Minimal heating time.",
            ),
            condition_heating_time_below: Optional[float] = Query(
                None, description="Maximal heating time.",
            ),
            condition_heating_atmosphere: Optional[List[str]] = Query(
                None, description="Required heating atmosphere, such as 'air', 'argon'.",
            ),
            condition_mixing_device: Optional[List[str]] = Query(
                None, description="Required mixing device, such as 'zirconia', 'Al2O3'.",
            ),
            condition_mixing_media: Optional[List[str]] = Query(
                None, description="Required mixing media, such as 'alcohol', 'water'.",
            ),
    ) -> STORE_PARAMS:
        crit = defaultdict(dict)  # type: dict
        if condition_heating_temperature_above:
            crit["operations.conditions.heating_temperature.values"]['$gte'] = condition_heating_temperature_above
        if condition_heating_temperature_below:
            crit["operations.conditions.heating_temperature.values"]['$lte'] = condition_heating_temperature_below
        if condition_heating_time_above:
            crit["operations.conditions.heating_time"]['$gte'] = condition_heating_time_above
        if condition_heating_time_below:
            crit["operations.conditions.heating_time"]['$lte'] = condition_heating_time_below
        if condition_heating_atmosphere:
            crit["operations.conditions.heating_atmosphere"]['$all'] = condition_heating_atmosphere
        if condition_mixing_device:
            crit["operations.conditions.mixing_device"]['$all'] = condition_mixing_device
        if condition_mixing_media:
            crit["operations.conditions.mixing_media"]['$all'] = condition_mixing_media

        return {"criteria": crit}

    def ensure_indexes(self):
        return [
            ("operations.conditions.heating_temperature.values", False),
            ("operations.conditions.heating_time.values", False),
            ("operations.conditions.heating_atmosphere", False),
            ("operations.conditions.mixing_device", False),
            ("operations.conditions.mixing_media", False),
        ]
