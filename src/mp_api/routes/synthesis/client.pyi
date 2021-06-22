from typing import List, Optional
from mp_api.routes.synthesis.models import SynthesisSearchResultModel


class SynthesisRester:

    def get_document_by_id(
        self,
        document_id: str,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
    ) -> SynthesisSearchResultModel: ...
