from typing import List, Optional
from emmet.core.thermo import ThermoDoc


class ThermoRester:

    def get_document_by_id(
        self, document_id: str, fields: Optional[List[str]] = None, monty_decode: bool = True,
    ) -> ThermoDoc: ...
