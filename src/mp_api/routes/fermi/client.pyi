from typing import List, Optional
from mp_api.routes.fermi.models import FermiDoc


class FermiRester:

    def get_document_by_id(
        self,
        document_id: str,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
    ) -> FermiDoc: ...
