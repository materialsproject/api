from mp_api.routes.piezo.query_operators import PiezoelectricQuery

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_piezo_query():
    op = PiezoelectricQuery()

    assert op.query(piezo_modulus_min=0, piezo_modulus_max=5) == {
        "criteria": {"piezo.e_ij_max": {"$gte": 0, "$lte": 5}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(piezo_modulus_min=0, piezo_modulus_max=5) == {
            "criteria": {"piezo.e_ij_max": {"$gte": 0, "$lte": 5}}
        }
