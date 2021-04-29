from typing import List, Optional
from mp_api.routes.robocrys.models import RobocrysDoc


class RobocrysRester:
    def query_by_task_id(
        self, task_id, fields: Optional[List[str]] = None, monty_decode: bool = True
    ) -> RobocrysDoc:
        ...
