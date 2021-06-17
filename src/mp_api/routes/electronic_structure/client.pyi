from typing import List, Optional
from emmet.core.electronic_structure import ElectronicStructureDoc


class ElectronicStructureRester:

    def get_document_by_id(
        self,
        document_id: str,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
    ) -> ElectronicStructureDoc: ...


class BandStructureRester:

    def get_document_by_id(
        self,
        document_id: str,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
    ) -> ElectronicStructureDoc: ...


class DosRester:

    def get_document_by_id(
        self,
        document_id: str,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
    ) -> ElectronicStructureDoc: ...
