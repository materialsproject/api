from mp_api.core.client import BaseRester
from mp_api.routes.dois.models import DOIDoc


class DOIRester(BaseRester[DOIDoc]):

    suffix = "doi"
    document_model = DOIDoc  # type: ignore
    primary_key = "task_id"
