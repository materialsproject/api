"""Test basic molecules functionality.

This class currently is only functional as an access
point for other resters, therefore we include only basic tests here.
"""

from mp_api.client.routes.molecules.molecules import MoleculeRester
from mp_api.client.routes.molecules import MOLECULES_RESTERS


def test_molecule_rester():
    with MoleculeRester() as rester:
        assert all(sub_rester in dir(rester) for sub_rester in MOLECULES_RESTERS)

        assert all(
            getattr(rester, k)._class_name == lazy_obj._class_name
            for k, lazy_obj in MOLECULES_RESTERS.items()
        )
