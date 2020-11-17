from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester, MPRestError

import warnings


class RobocrysRester(BaseRester):

    suffix = "robocrys"