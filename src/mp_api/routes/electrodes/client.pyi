from typing import List, Optional
from emmet.core.electrode import InsertionElectrodeDoc


class ElectrodeRester:

    def query_by_task_id(
        self, task_id, fields: Optional[List[str]] = None, monty_decode: bool = True
    ) -> InsertionElectrodeDoc: ...
