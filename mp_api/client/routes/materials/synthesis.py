from __future__ import annotations

import pyarrow as pa
from emmet.core.arrow import arrowize
from emmet.core.synthesis import (
    OperationTypeEnum,
    SynthesisRecipe,
    SynthesisSearchResultModel,
    SynthesisTypeEnum,
)

from mp_api.client.core import BaseRester, MPRestError


class SynthesisRester(BaseRester):
    suffix = "materials/synthesis"
    document_model = SynthesisSearchResultModel  # type: ignore

    def _download_schema(self) -> pa.Schema:
        """Full downloads hold recipes only: `search_score` and `highlights`
        are added by the text search and aren't stored on S3 (they load as None).
        """
        return pa.schema(arrowize(SynthesisRecipe))

    def search(
        self,
        keywords: list[str] | None = None,
        synthesis_type: list[SynthesisTypeEnum] | None = None,
        target_formula: str | None = None,
        precursor_formula: str | None = None,
        operations: list[OperationTypeEnum] | None = None,
        condition_heating_temperature_min: float | None = None,
        condition_heating_temperature_max: float | None = None,
        condition_heating_time_min: float | None = None,
        condition_heating_time_max: float | None = None,
        condition_heating_atmosphere: list[str] | None = None,
        condition_mixing_device: list[str] | None = None,
        condition_mixing_media: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int | None = 10,
    ) -> list[SynthesisSearchResultModel] | list[dict]:
        """Search synthesis recipe text.

        Arguments:
            keywords (list[str] | None): List of string keywords to search synthesis paragraph text with
            synthesis_type (list[SynthesisTypeEnum] | None): Type of synthesis to include
            target_formula (str | None): Chemical formula of the target material
            precursor_formula (str | None): Chemical formula of the precursor material
            operations (list[OperationTypeEnum] | None): List of operations that syntheses must have
            condition_heating_temperature_min (float | None): Minimal heating temperature
            condition_heating_temperature_max (float | None): Maximal heating temperature
            condition_heating_time_min (float | None): Minimal heating time
            condition_heating_time_max (float | None): Maximal heating time
            condition_heating_atmosphere (list[str] | None): Required heating atmosphere, such as "air", "argon"
            condition_mixing_device (list[str] | None): Required mixing device, such as "zirconia", "Al2O3".
            condition_mixing_media (list[str] | None): Required mixing media, such as "alcohol", "water"
            num_chunks (int | None): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int | None): Number of data entries per chunk.

        With no search terms and `num_chunks=None`, every recipe is downloaded from
        S3 as a local dataset instead; `search_score` and `highlights` are then None.

        Returns:
            ([SynthesisSearchResultModel], [dict]): List of synthesis documents or dictionaries.
        """
        # Turn None and empty list into None
        keywords = keywords or None
        synthesis_type = synthesis_type or None
        operations = operations or None
        condition_heating_atmosphere = condition_heating_atmosphere or None
        condition_mixing_device = condition_mixing_device or None
        condition_mixing_media = condition_mixing_media or None

        if keywords:
            keywords = ",".join([word.strip() for word in keywords])  # type: ignore

        synthesis_docs = self._query_resource(
            criteria={
                "keywords": keywords,
                "synthesis_type": synthesis_type,
                "target_formula": target_formula,
                "precursor_formula": precursor_formula,
                "operations": operations,
                "condition_heating_temperature_min": condition_heating_temperature_min,
                "condition_heating_temperature_max": condition_heating_temperature_max,
                "condition_heating_time_min": condition_heating_time_min,
                "condition_heating_time_max": condition_heating_time_max,
                "condition_heating_atmosphere": condition_heating_atmosphere,
                "condition_mixing_device": condition_mixing_device,
                "condition_mixing_media": condition_mixing_media,
                "_limit": chunk_size,
            },
            chunk_size=chunk_size,
            num_chunks=num_chunks,
        ).get("data", None)

        if synthesis_docs is None:
            raise MPRestError("Cannot find any matches.")

        return synthesis_docs
