from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester, MPRestError
from mp_api.robocrys.models import RobocrysDoc

import warnings


class RobocrysRester(BaseRester):

    suffix = "robocrys"
    document_model = RobocrysDoc
