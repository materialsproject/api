from mp_api.core.client import BaseRester
from mp_api.routes.synthesis.models import SynthesisRecipe


class SynthesisRester(BaseRester):

    suffix = "synthesis"
    document_model = SynthesisRecipe
