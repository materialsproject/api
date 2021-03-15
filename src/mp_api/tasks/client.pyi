from typing import List, Optional
from mp_api.tasks.models import TaskDoc


class TaskRester:
    def query_by_task_id(
        self, task_id, fields: Optional[List[str]] = None, monty_decode: bool = True
    ) -> TaskDoc:
        ...
