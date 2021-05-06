from mp_api.core.client import BaseRester
from emmet.core.electrode import InsertionElectrodeDoc


class ElectrodeRester(BaseRester):

    suffix = "insertion_electrodes"
    document_model = InsertionElectrodeDoc
