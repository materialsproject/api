from mp_api.core.client import BaseRester
from mp_api.synth.models import SynthDoc


class SynthRester(BaseRester):

    suffix = "synth"
    document_model = SynthDoc
