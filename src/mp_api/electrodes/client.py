from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.electrodes.models import InsertionElectrodeDoc

import warnings


class ElectrodeRester(BaseRester):

    suffix = "insertion_electrodes"
    document_model = InsertionElectrodeDoc

