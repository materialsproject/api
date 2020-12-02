from mp_api.core.client import BaseRester
from mp_api.synthesis.models import SynthesisDoc


class SynthesisRester(BaseRester):

    suffix = "synthesis"
    document_model = SynthesisDoc
