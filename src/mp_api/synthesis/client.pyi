from typing import List
from mp_api.synthesis.models import SynthesisDoc


class SynthesisRester:

    def query_text(self, keywords: List[str]) -> SynthesisDoc:
        ...
