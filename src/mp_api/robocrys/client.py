from mp_api.core.client import BaseRester
from mp_api.robocrys.models import RobocrysDoc


class RobocrysRester(BaseRester):

    suffix = "robocrys"
    document_model = RobocrysDoc
