from mp_api.routes.bonds.query_operators import BondLengthQuery, CoordinationEnvsQuery

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_bond_length_query_operator():
    op = BondLengthQuery()

    q = op.query(
        max_bond_length_min=0,
        max_bond_length_max=5,
        min_bond_length_min=0,
        min_bond_length_max=5,
        mean_bond_length_min=0,
        mean_bond_length_max=5,
    )

    fields = [
        "bond_length_stats.min",
        "bond_length_stats.max",
        "bond_length_stats.mean",
    ]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            max_bond_length_min=0,
            max_bond_length_max=5,
            min_bond_length_min=0,
            min_bond_length_max=5,
            mean_bond_length_min=0,
            mean_bond_length_max=5,
        )
        assert dict(q) == {
            "criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}
        }


def test_coordination_envs_query():
    op = CoordinationEnvsQuery()

    assert op.query(
        coordination_envs="Mo-S(6),S-Mo(3)",
        coordination_envs_anonymous="A-B(6),A-B(3)",
    ) == {
        "criteria": {
            "coordination_envs": {"$all": ["Mo-S(6)", "S-Mo(3)"]},
            "coordination_envs_anonymous": {"$all": ["A-B(6)", "A-B(3)"]},
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(
            coordination_envs="Mo-S(6),S-Mo(3)",
            coordination_envs_anonymous="A-B(6),A-B(3)",
        ) == {
            "criteria": {
                "coordination_envs": {"$all": ["Mo-S(6)", "S-Mo(3)"]},
                "coordination_envs_anonymous": {"$all": ["A-B(6)", "A-B(3)"]},
            }
        }

