from typing import List, Optional

from mp_api.routes.synthesis.models import (
    SynthesisTypeEnum, OperationTypeEnum, SynthesisSearchResultModel
)


class SynthesisRester:

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
    ) -> SynthesisSearchResultModel: ...
