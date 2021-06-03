import re
from typing import List, Optional, Any, Dict, Union

from fastapi import Query
from pydantic import Field
from pymatgen.core import Composition

from mp_api.core.models import Response
from mp_api.core.resource import GetResource
from mp_api.core.utils import api_sanitize
from mp_api.routes.synthesis.models import SynthesisRecipe, SynthesisTypeEnum, OperationTypeEnum

synth_indexes = [
    ("synthesis_type", False),
    ("targets_formula_s", False),
    ("precursors_formula_s", False),
    ("operations.type", False),
    ("operations.conditions.heating_temperature.values", False),
    ("operations.conditions.heating_time.values", False),
    ("operations.conditions.heating_atmosphere", False),
    ("operations.conditions.mixing_device", False),
    ("operations.conditions.mixing_media", False),
]


class ResultModel(SynthesisRecipe):
    search_score: Optional[float] = Field(
        None,
        description="Search score.",
    )
    highlights: Optional[List[Any]] = Field(
        None,
        description="Search highlights.",
    )


def make_ellipsis(text, limit=100, remove_trailing=True):
    if len(text) > limit:
        if remove_trailing:
            text = text[:limit]
            # Make results nicer by cutting incomplete words of max 15 characters.
            # For example: "This is an incomplete sente" becomes "This is an incomplete "
            trailing = re.search(r"(?<![\w\d])[\w\d]{,15}$", text)
            if trailing is not None:
                text = text[:trailing.start()] + "..."
        else:
            text = text[len(text) - limit:]
            heading = re.search(r"^[\w\d]{,15}(?![\w\d])", text)
            if heading is not None:
                text = "..." + text[heading.end():]
    return text


def mask_paragraphs(doc, limit=100):
    if isinstance(doc.get("paragraph_string", None), str):
        doc["paragraph_string"] = make_ellipsis(doc["paragraph_string"], limit=limit)

    return doc


def mask_highlights(doc, limit=100):
    if isinstance(doc.get("highlights", None), list):
        total_chars = 0
        show_hl = []

        for h_obj in doc["highlights"]:
            if total_chars >= limit:
                break
            hls = h_obj["texts"]

            # Identify where the highlighting starts.
            for i, hl in enumerate(hls):
                if hl['type'] == 'hit':
                    if i > 0:
                        hls[i - 1]["value"] = make_ellipsis(hls[i - 1]["value"], limit=20, remove_trailing=False)
                        hls = hls[i - 1:]
                    break

            # Remove excessive chars after the hit.
            for i, hl in enumerate(hls):
                total_chars += len(hl["value"])
                if total_chars >= limit:
                    hl_limit = max(1, limit - (total_chars - len(hl["value"])))
                    hl["value"] = make_ellipsis(hl["value"], limit=hl_limit)
                    hls = hls[:i + 1]
                    break
            h_obj["texts"] = hls
            show_hl.append(h_obj)

        doc["highlights"] = show_hl

    return doc


def synth_resource(synth_store):
    def custom_synth_prep(self):
        async def query_synth_text(
                keywords: Optional[str] = Query(
                    None, description="String keywords to search synthesis paragraph text with."),
                synthesis_type: Optional[List[SynthesisTypeEnum]] = Query(
                    None, description="Type of synthesis to include."),
                target_formula: Optional[str] = Query(
                    None, description="Chemical formula of the target material."),
                precursor_formula: Optional[str] = Query(
                    None, description="Chemical formula of the precursor material."),

                operations: Optional[List[OperationTypeEnum]] = Query(
                    None, description="List of operations that syntheses must have."),
                condition_heating_temperature_min: Optional[float] = Query(
                    None, description="Minimal heating temperature."),
                condition_heating_temperature_max: Optional[float] = Query(
                    None, description="Maximal heating temperature."),
                condition_heating_time_min: Optional[float] = Query(
                    None, description="Minimal heating time."),
                condition_heating_time_max: Optional[float] = Query(
                    None, description="Maximal heating time."),
                condition_heating_atmosphere: Optional[List[str]] = Query(
                    None, description='Required heating atmosphere, such as "air", "argon".'),
                condition_mixing_device: Optional[List[str]] = Query(
                    None, description='Required mixing device, such as "zirconia", "Al2O3".'),
                condition_mixing_media: Optional[List[str]] = Query(
                    None, description='Required mixing media, such as "alcohol", "water".'),

                skip: int = Query(0, description="Number of entries to skip in the search"),
                limit: int = Query(10, description="Max number of entries to return in a single query. Limited to 10."),
        ):
            project_dict: Dict[str, Union[Dict, int]] = {
                "_id": 0,
                "doi": 1,
                "synthesis_type": 1,
                "reaction": 1,
                "reaction_string": 1,
                "operations": 1,
                "target": 1,
                "targets_formula": 1,
                "targets_formula_s": 1,
                "precursors": 1,
                "precursors_formula_s": 1,
                "paragraph_string": 1,
            }

            pipeline: List[Any] = []
            if keywords:
                pipeline.append({
                    "$search": {
                        # NOTICE to MongoDB admin:
                        # This MongoDB Atlas index should be created with:
                        # {"mappings": { "dynamic": false,
                        #   "fields": {
                        #     "paragraph_string": {"type": "string"}
                        #   }}}
                        "index": "synth_descriptions",
                        "search": {
                            "query": keywords,
                            "path": "paragraph_string",
                        },
                        "highlight": {
                            "path": "paragraph_string",
                            # "maxNumPassages": 1
                        }
                    }
                })
                project_dict.update({
                    "search_score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                })
            pipeline.append({
                "$project": project_dict
            })

            crit: Dict[str, Any] = {}
            if synthesis_type:
                crit["synthesis_type"] = {"$in": synthesis_type}
            if target_formula:
                reduced_formula = Composition(target_formula).get_reduced_formula_and_factor()[0]
                crit["targets_formula_s"] = reduced_formula
            if precursor_formula:
                reduced_formula = Composition(precursor_formula).get_reduced_formula_and_factor()[0]
                crit["precursors_formula_s"] = reduced_formula
            if operations:
                crit["operations.type"] = {"$all": operations}
            if condition_heating_temperature_min:
                crit["operations.conditions.heating_temperature.values"] = {
                    "$gte": condition_heating_temperature_min}
            if condition_heating_temperature_max:
                crit["operations.conditions.heating_temperature.values"] = {
                    "$lte": condition_heating_temperature_max}
            if condition_heating_time_min:
                crit["operations.conditions.heating_time.values"] = {
                    "$gte": condition_heating_time_min}
            if condition_heating_time_max:
                crit["operations.conditions.heating_time.values"] = {
                    "$lte": condition_heating_time_max}
            if condition_heating_atmosphere:
                crit["operations.conditions.heating_atmosphere"] = {
                    "$all": condition_heating_atmosphere}
            if condition_mixing_device:
                crit["operations.conditions.mixing_device"] = {
                    "$all": condition_mixing_device}
            if condition_mixing_media:
                crit["operations.conditions.mixing_media"] = {
                    "$all": condition_mixing_media}

            if crit:
                pipeline.append({"$match": crit})

            self.store.connect()
            # for index_name, unique in synth_indexes:
            #     self.store.ensure_index(index_name, unique)

            try:
                total = next(self.store._collection.aggregate(
                    pipeline + [{"$count": "total"}], allowDiskUse=True))["total"]

                pipeline.extend([
                    {"$sort": {"search_score": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ])

                data = list(self.store._collection.aggregate(pipeline, allowDiskUse=True))
                for doc in data:
                    mask_highlights(doc)
                    mask_paragraphs(doc)
            except StopIteration:
                total = 0
                data = []

            response = {
                "data": data,
                "meta": {
                    "total": total
                }}

            return response

        self.router.get(
            "/recipes/",
            response_model=Response[api_sanitize(ResultModel, allow_dict_msonable=True)],
            response_model_exclude_unset=True,
            response_description="Find synthesis description documents through text search.",
            tags=self.tags,
        )(query_synth_text)

    resource = GetResource(
        synth_store,
        SynthesisRecipe,
        tags=["Synthesis"],
        custom_endpoint_funcs=[custom_synth_prep],
        enable_default_search=False,
        enable_get_by_key=False,
    )

    return resource
