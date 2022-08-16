from mp_api.client.core import BaseRester
from emmet.core.phonon import PhononBSDOSDoc


class PhononRester(BaseRester[PhononBSDOSDoc]):

    suffix = "phonon"
    document_model = PhononBSDOSDoc  # type: ignore
    primary_key = "material_id"

    def search(*args, **kwargs):  # pragma: no cover
        raise NotImplementedError(
            """
            The PhononRester.search method does not exist as no search endpoint is present.
            Use get_data_by_id instead.
            """
        )
