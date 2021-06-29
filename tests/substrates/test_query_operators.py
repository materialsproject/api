from mp_api.routes.substrates.query_operators import (
    SubstrateStructureQuery,
    EnergyAreaQuery,
)


from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_substrate_structure_operator():
    op = SubstrateStructureQuery()

    assert op.query(film_orientation="0,1, 1", substrate_orientation="1, 0,1") == {
        "criteria": {"film_orient": "0 1 1", "orient": "1 0 1"}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert new_op.query(
            film_orientation="0,1, 1", substrate_orientation="1, 0,1"
        ) == {"criteria": {"film_orient": "0 1 1", "orient": "1 0 1"}}


def test_energy_area_operator():
    op = EnergyAreaQuery()

    q = op.query(area_min=0, area_max=5, energy_min=0, energy_max=5)

    fields = ["area", "energy"]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(area_min=0, area_max=5, energy_min=0, energy_max=5)
        assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}
