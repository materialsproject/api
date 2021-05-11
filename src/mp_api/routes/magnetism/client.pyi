from typing import List, Optional
from mp_api.routes.magnetism.models import MagnetismDoc


class MagnetismRester:

    def query_by_task_id(
        self, task_id, fields: Optional[List[str]] = None, monty_decode: bool = True
    ) -> MagnetismDoc: ...
