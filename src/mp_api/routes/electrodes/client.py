from mp_api.core.client import BaseRester
from mp_api.routes.electrodes.models import InsertionElectrodeDoc


class ElectrodeRester(BaseRester):

    suffix = "insertion_electrodes"
    document_model = InsertionElectrodeDoc
