from mp_api.routes.oxidation_states.query_operators import PossibleOxiStateQuery

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_possible_oxi_state_query():
    op = PossibleOxiStateQuery()

    assert op.query(possible_species="Cr2+, O2-") == {
        "criteria": {"possible_species": {"$all": ["Cr2+", "O2-"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert op.query(possible_species="Cr2+, O2-") == {
            "criteria": {"possible_species": {"$all": ["Cr2+", "O2-"]}}
        }
