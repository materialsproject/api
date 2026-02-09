"""Define routes to non-core molecules resters."""
from __future__ import annotations

from mp_api.client.core.utils import LazyImport

MOLECULES_RESTERS: dict[str, LazyImport] = {
    k: LazyImport(f"mp_api.client.routes.molecules.{k}.{v}")
    for k, v in (
        ("jcesr", "JcesrMoleculesRester"),
        ("summary", "MoleculesSummaryRester"),
    )
}
