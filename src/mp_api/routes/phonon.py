from mp_api.core.client import BaseRester
from emmet.core.phonon import PhononBSDOSDoc


class PhononRester(BaseRester[PhononBSDOSDoc]):

    suffix = "phonon"
    document_model = PhononBSDOSDoc  # type: ignore
    primary_key = "material_id"
