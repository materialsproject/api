from typing import List, Optional
from emmet.core.xas import XASDoc


class XASRester:

    def get_document_by_id(
            self,
            document_id: str,
            fields: Optional[List[str]] = None,
            monty_decode: bool = True,
    ) -> XASDoc:
        ...
