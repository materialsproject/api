from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn

from mp_api.routes.molecules.query_operators import (
    MoleculeBaseQuery,
    MoleculeElementsQuery,
    MoleculeFormulaQuery,
)


def test_molecule_elements_query():
    op = MoleculeElementsQuery()

    assert op.query(elements="Si, O, P") == {
        "criteria": {"elements": {"$all": ["Si", "O", "P"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(elements="Si, O, P") == {
            "criteria": {"elements": {"$all": ["Si", "O", "P"]}}
        }


def test_molecule_base_query():
    op = MoleculeBaseQuery()

    q = op.query(
        nelements_min=0,
        nelements_max=5,
        EA_min=0,
        EA_max=5,
        IE_min=0,
        IE_max=5,
        charge_min=0,
        charge_max=5,
        pointgroup="C3v",
        smiles="CN=C=O",
    )

    fields = [
        "nelements",
        "EA",
        "IE",
        "charge",
    ]

    c = {field: {"$gte": 0, "$lte": 5} for field in fields}

    assert q == {"criteria": {"pointgroup": "C3v", "smiles": "CN=C=O", **c}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            nelements_min=0,
            nelements_max=5,
            EA_min=0,
            EA_max=5,
            IE_min=0,
            IE_max=5,
            charge_min=0,
            charge_max=5,
            pointgroup="C3v",
            smiles="CN=C=O",
        )
        c = {field: {"$gte": 0, "$lte": 5} for field in fields}

        assert q == {"criteria": {"pointgroup": "C3v", "smiles": "CN=C=O", **c}}


def test_molecule_formula_query():
    op = MoleculeFormulaQuery()

    assert op.query(formula="C6H12O6") == {"criteria": {"formula_pretty": "H2CO"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(formula="C6H12O6") == {
            "criteria": {"formula_pretty": "H2CO"}
        }
