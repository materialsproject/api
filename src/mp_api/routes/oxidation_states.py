from mp_api.core.client import BaseRester
from emmet.core.oxidation_states import OxidationStateDoc


class OxidationStatesRester(BaseRester[OxidationStateDoc]):

    suffix = "oxidation_states"
    document_model = OxidationStateDoc  # type: ignore
    primary_key = "material_id"
