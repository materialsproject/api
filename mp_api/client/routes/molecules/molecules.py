"""Define core molecules functionality.

Note that the `MoleculeRester`, unlike the `MaterialsRester`,
has no API functionality beyond serving as an access point for
the JCESR and summary resters.
"""

from __future__ import annotations

from emmet.core.qchem.molecule import MoleculeDoc

from mp_api.client.core.client import CoreRester
from mp_api.client.routes.molecules import MOLECULES_RESTERS


class MoleculeRester(CoreRester):
    """Define molecules stub for accessing JCESR and summary data."""

    document_model = MoleculeDoc
    primary_key = "molecule_id"
    suffix = "molecules/core"
    _sub_resters = MOLECULES_RESTERS
