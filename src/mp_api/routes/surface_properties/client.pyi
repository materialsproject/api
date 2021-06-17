from typing import List, Optional
from mp_api.routes.surface_properties.models import SurfacePropDoc


class SurfacePropertiesRester:

    def get_document_by_id(
            self,
            document_id: str,
            fields: Optional[List[str]] = None,
            monty_decode: bool = True,
    ) -> SurfacePropDoc:
        ...
