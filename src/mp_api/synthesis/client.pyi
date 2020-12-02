from typing import List
from mp_api.synthesis.models import SynthDoc


class SynthsRester:
    def query_text(self, keywords: List[str]) -> SynthDoc:
        ...
