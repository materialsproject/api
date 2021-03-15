from typing import List, Optional
from mp_api.thermo.models import ThermoDoc


class ThermoRester:
    def query_by_task_id(
        self, task_id, fields: Optional[List[str]] = None, monty_decode: bool = True
    ) -> ThermoDoc:
        ...
