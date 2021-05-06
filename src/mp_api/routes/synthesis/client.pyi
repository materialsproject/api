from typing import List
from mp_api.routes.synthesis.models import SynthesisDoc


class SynthesisRester:

    def query_text(self, keywords: List[str]) -> SynthesisDoc:
        ...
