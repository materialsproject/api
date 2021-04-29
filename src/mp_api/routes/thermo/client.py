from mp_api.core.client import BaseRester
from mp_api.routes.thermo.models import ThermoDoc


class ThermoRester(BaseRester):

    suffix = "thermo"
    document_model = ThermoDoc
    supports_versions = True


# TODO: Add new search method
