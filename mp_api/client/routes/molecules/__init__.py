from __future__ import annotations

from mp_api.client.core.utils import LazyImport

MOLECULES_RESTERS = {
    k: LazyImport(f"mp_api.client.routes.molecules.{k}.{v}")
    for k, v in (
        ("molecules", "MoleculeRester"),
        ("jcser", "JcesrMoleculesRester"),
        ("summary", "MoleculesSummaryRester"),
    )
}
