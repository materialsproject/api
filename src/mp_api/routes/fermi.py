from emmet.core.fermi import FermiDoc
from mp_api.core.client import BaseRester


class FermiRester(BaseRester[FermiDoc]):

    suffix = "fermi"
    document_model = FermiDoc  # type: ignore
    primary_key = "task_id"
