from mp_api.routes.phonon.query_operators import PhononImgQuery

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_phonon_image_query():
    op = PhononImgQuery()

    assert op.query(task_id="mp-149") == {"criteria": {"task_id": "mp-149"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(task_id="mp-149") == {"criteria": {"task_id": "mp-149"}}
