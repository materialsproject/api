"""Test basic molecules functionality.

This class currently is non-functional, except as an access
point for other resters, therefore we include only basic tests here.
"""

from mp_api.client.routes.molecules.molecules import BaseMoleculeRester, MoleculeRester
from mp_api.client.routes.molecules import MOLECULES_RESTERS


def test_molecule_rester():
    with MoleculeRester() as rester:
        assert set(dir(rester)) == set(
            dir(BaseMoleculeRester) + list(MOLECULES_RESTERS)
        )

        assert all(
            getattr(rester, k)._class_name == lazy_obj._class_name
            for k, lazy_obj in MOLECULES_RESTERS.items()
        )
