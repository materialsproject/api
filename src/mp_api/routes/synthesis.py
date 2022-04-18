from typing import List, Optional

from mp_api.core.client import BaseRester, MPRestError
from emmet.core.synthesis import (
    SynthesisSearchResultModel,
    SynthesisTypeEnum,
    OperationTypeEnum,
)


class SynthesisRester(BaseRester[SynthesisSearchResultModel]):
    suffix = "synthesis"
    document_model = SynthesisSearchResultModel  # type: ignore

    def search_synthesis_text(
        self,
        keywords: Optional[List[str]] = None,
        synthesis_type: Optional[List[SynthesisTypeEnum]] = None,
        target_formula: Optional[str] = None,
        precursor_formula: Optional[str] = None,
        operations: Optional[List[OperationTypeEnum]] = None,
        condition_heating_temperature_min: Optional[float] = None,
        condition_heating_temperature_max: Optional[float] = None,
        condition_heating_time_min: Optional[float] = None,
        condition_heating_time_max: Optional[float] = None,
        condition_heating_atmosphere: Optional[List[str]] = None,
        condition_mixing_device: Optional[List[str]] = None,
        condition_mixing_media: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: Optional[int] = 10,
    ):
        """
        Search synthesis recipe text.
        Arguments:
            keywords (Optional[List[str]]): List of string keywords to search synthesis paragraph text with
            synthesis_type (Optional[List[SynthesisTypeEnum]]): Type of synthesis to include
            target_formula (Optional[str]): Chemical formula of the target material
            precursor_formula (Optional[str]): Chemical formula of the precursor material
            operations (Optional[List[OperationTypeEnum]]): List of operations that syntheses must have
            condition_heating_temperature_min (Optional[float]): Minimal heating temperature
            condition_heating_temperature_max (Optional[float]): Maximal heating temperature
            condition_heating_time_min (Optional[float]): Minimal heating time
            condition_heating_time_max (Optional[float]): Maximal heating time
            condition_heating_atmosphere (Optional[List[str]]): Required heating atmosphere, such as "air", "argon"
            condition_mixing_device (Optional[List[str]]): Required mixing device, such as "zirconia", "Al2O3".
            condition_mixing_media (Optional[List[str]]): Required mixing media, such as "alcohol", "water"
            num_chunks (Optional[int]): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (Optional[int]): Number of data entries per chunk.
        Returns:
            synthesis_docs ([SynthesisDoc]): List of synthesis documents
        """

        # Turn None and empty list into None
        keywords = keywords or None
        synthesis_type = synthesis_type or None
        operations = operations or None
        condition_heating_atmosphere = condition_heating_atmosphere or None
        condition_mixing_device = condition_mixing_device or None
        condition_mixing_media = condition_mixing_media or None

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
