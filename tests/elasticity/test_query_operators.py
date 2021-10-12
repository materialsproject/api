from mp_api.routes.elasticity.query_operators import (
    BulkModulusQuery,
    ShearModulusQuery,
    PoissonQuery,
    ChemsysQuery,
)

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_bulk_modulus_query():
    op = BulkModulusQuery()

    q = op.query(
        k_voigt_min=0,
        k_voigt_max=5,
        k_reuss_min=0,
        k_reuss_max=5,
        k_vrh_min=0,
        k_vrh_max=5,
    )

    fields = ["elasticity.k_voigt", "elasticity.k_reuss", "elasticity.k_vrh"]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            k_voigt_min=0,
            k_voigt_max=5,
            k_reuss_min=0,
            k_reuss_max=5,
            k_vrh_min=0,
            k_vrh_max=5,
        )
        assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}


def test_shear_modulus_query():
    op = ShearModulusQuery()

    q = op.query(
        g_voigt_min=0,
        g_voigt_max=5,
        g_reuss_min=0,
        g_reuss_max=5,
        g_vrh_min=0,
        g_vrh_max=5,
    )

    fields = ["elasticity.g_voigt", "elasticity.g_reuss", "elasticity.g_vrh"]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            g_voigt_min=0,
            g_voigt_max=5,
            g_reuss_min=0,
            g_reuss_max=5,
            g_vrh_min=0,
            g_vrh_max=5,
        )
        assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}


def test_poisson_query():
    op = PoissonQuery()

    q = op.query(
        elastic_anisotropy_min=0,
        elastic_anisotropy_max=5,
        poisson_min=0,
        poisson_max=5,
    )

    fields = ["elasticity.universal_anisotropy", "elasticity.homogeneous_poisson"]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            elastic_anisotropy_min=0,
            elastic_anisotropy_max=5,
            poisson_min=0,
            poisson_max=5,
        )
        assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}


def test_chemsys_query():
    op = ChemsysQuery()

    assert op.query(chemsys="Fe-Bi-O") == {"criteria": {"chemsys": "Bi-Fe-O"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(chemsys="Fe-Bi-O") == {"criteria": {"chemsys": "Bi-Fe-O"}}
