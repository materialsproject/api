"""Test basic molecules functionality."""

from mp_api.client.routes.molecules.molecules import BaseMoleculeRester, MoleculeRester
from mp_api.client.routes.molecules import MOLECULES_RESTERS


def test_molecule_rester():
    assert set(dir(MoleculeRester())) == set(
        dir(BaseMoleculeRester) + list(MOLECULES_RESTERS)
    )
