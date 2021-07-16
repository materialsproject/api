from maggma.api import query_operator
from mp_api.routes.dielectric.query_operators import DielectricQuery

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_dielectric_query_operator():
    op = DielectricQuery()

    q = op.query(
        e_total_min=0,
        e_total_max=5,
        e_electronic_min=0,
        e_electronic_max=5,
        e_ionic_min=0,
        e_ionic_max=5,
        n_min=0,
        n_max=5,
    )

    fields = [
        "dielectric.e_total",
        "dielectric.e_ionic",
        "dielectric.e_electronic",
        "dielectric.n",
    ]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            e_total_min=0,
            e_total_max=5,
            e_electronic_min=0,
            e_electronic_max=5,
            e_ionic_min=0,
            e_ionic_max=5,
            n_min=0,
            n_max=5,
        )
        assert dict(q) == {
            "criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}
        }
