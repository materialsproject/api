from typing import List, Optional
from mp_api.routes.materials.models.doc import MaterialsCoreDoc

class MaterialsRester:
    def query_by_task_id(
        self, task_id, fields: Optional[List[str]] = None, monty_decode: bool = True
    ) -> MaterialsCoreDoc: ...
    def get_structure_by_material_id(material_id): ...

