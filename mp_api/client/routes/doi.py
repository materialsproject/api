from mp_api.client.core import BaseRester
from emmet.core.dois import DOIDoc


class DOIRester(BaseRester[DOIDoc]):

    suffix = "doi"
    document_model = DOIDoc  # type: ignore
    primary_key = "task_id"

    def search(*args, **kwargs):  # pragma: no cover
        raise NotImplementedError(
            """
            The DOIRester.search method does not exist as no search endpoint is present. Use get_data_by_id instead.
            """
        )
