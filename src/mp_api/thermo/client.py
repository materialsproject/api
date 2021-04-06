from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.thermo.models import ThermoDoc

import warnings


class ThermoRester(BaseRester):

    suffix = "thermo"
    document_model = ThermoDoc
    supports_versions = True


# TODO: Add new search method
