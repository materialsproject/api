from mp_api.routes.charge_density.query_operators import ChgcarTaskIDQuery
from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_chgcar_test_id_query():
    op = ChgcarTaskIDQuery()

    assert op.query(task_ids="mp-149, mp-13") == {
        "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(task_ids="mp-149, mp-13") == {
            "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
        }
