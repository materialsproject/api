from mp_api.core.client import BaseRester
from emmet.core.dois import DOIDoc


class DOIRester(BaseRester[DOIDoc]):

    suffix = "doi"
    document_model = DOIDoc  # type: ignore
    primary_key = "task_id"
