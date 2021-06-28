from fastapi.param_functions import Form
from mp_api.routes.materials.query_operators import (
    FormulaQuery,
    ElementsQuery,
    DeprecationQuery,
    SymmetryQuery,
)
from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn

from emmet.core.symmetry import CrystalSystem


def test_formula_query():
    op = FormulaQuery()
    assert op.query("Si2O4") == {
        "criteria": {
            "composition_reduced.O": 2.0,
            "composition_reduced.Si": 1.0,
            "nelements": 2,
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query("Si2O4") == {
            "criteria": {
                "composition_reduced.O": 2.0,
                "composition_reduced.Si": 1.0,
                "nelements": 2,
            }
        }


def test_elements_query():
    eles = ["Si", "O"]
    neles = ["N", "P"]

    op = ElementsQuery()
    assert op.query(elements=",".join(eles), exclude_elements=",".join(neles)) == {
        "criteria": {"elements": {"$all": ["Si", "O"], "$nin": ["N", "P"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(
            elements=",".join(eles), exclude_elements=",".join(neles)
        ) == {"criteria": {"elements": {"$all": ["Si", "O"], "$nin": ["N", "P"],},}}


def test_deprecation_query():
    op = DeprecationQuery()
    assert op.query(True) == {"criteria": {"deprecated": True}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(True) == {"criteria": {"deprecated": True}}


def test_symmetry_query():
    op = SymmetryQuery()
    assert op.query(
        crystal_system=CrystalSystem.cubic,
        spacegroup_number=221,
        spacegroup_symbol="Pm3m",
    ) == {
        "criteria": {
            "symmetry.crystal_system": "Cubic",
            "symmetry.number": 221,
            "symmetry.symbol": "Pm3m",
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(
            crystal_system=CrystalSystem.cubic,
            spacegroup_number=221,
            spacegroup_symbol="Pm3m",
        ) == {
            "criteria": {
                "symmetry.crystal_system": "Cubic",
                "symmetry.number": 221,
                "symmetry.symbol": "Pm3m",
            }
        }
