from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn

from mp_api.routes.grain_boundary.query_operators import GBStructureQuery, GBTaskIDQuery
from mp_api.routes.grain_boundary.models import GBTypeEnum


def test_grain_boundary_structure_query():
    op = GBStructureQuery()

    assert op.query(
        sigma=0.5, type=GBTypeEnum.twist, chemsys="Si-Fe", pretty_formula="Fe2Si4"
    ) == {
        "criteria": {
            "sigma": 0.5,
            "type": "twist",
            "chemsys": "Fe-Si",
            "pretty_formula": "FeSi2",
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert op.query(
            sigma=0.5, type=GBTypeEnum.twist, chemsys="Si-Fe", pretty_formula="Fe2Si4"
        ) == {
            "criteria": {
                "sigma": 0.5,
                "type": "twist",
                "chemsys": "Fe-Si",
                "pretty_formula": "FeSi2",
            }
        }


def test_grain_boundary_task_id_query():
    op = GBTaskIDQuery()

    assert op.query(task_ids="mp-149, mp-13") == {
        "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(task_ids="mp-149, mp-13") == {
            "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
        }
