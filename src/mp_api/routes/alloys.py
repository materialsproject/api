from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from emmet.core.alloys import AlloyPairDoc

import warnings


class AlloysRester(BaseRester[AlloyPairDoc]):

    suffix = "alloys"
    document_model = AlloyPairDoc  # type: ignore
    primary_key = "material_id"
