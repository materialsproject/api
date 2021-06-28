import os

from mp_api.core.settings import MAPISettings
from mp_api.routes.materials.query_operators import (
    FormulaQuery,
    ElementsQuery,
    DeprecationQuery,
    SymmetryQuery,
    MultiTaskIDQuery,
    MultiMaterialIDQuery,
    FindStructureQuery,
    FormulaAutoCompleteQuery,
)
from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn

from emmet.core.symmetry import CrystalSystem
from pymatgen.core.structure import Structure


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
        ) == {"criteria": {"elements": {"$all": ["Si", "O"], "$nin": ["N", "P"]}}}


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


def test_multi_task_id_query():
    op = MultiTaskIDQuery()
    assert op.query(task_ids="mp-149, mp-13") == {
        "criteria": {"task_ids": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(task_ids="mp-149, mp-13") == {
            "criteria": {"task_ids": {"$in": ["mp-149", "mp-13"]}}
        }


def test_multi_material_id_query():
    op = MultiMaterialIDQuery()
    assert op.query(material_ids="mp-149, mp-13") == {
        "criteria": {"material_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(material_ids="mp-149, mp-13") == {
            "criteria": {"material_id": {"$in": ["mp-149", "mp-13"]}}
        }


def test_find_structure_query():
    op = FindStructureQuery()

    structure = Structure.from_file(
        os.path.join(MAPISettings().test_files, "Si_mp_149.cif")
    )
    assert op.query(
        structure=structure.as_dict(), ltol=0.2, stol=0.3, angle_tol=5, limit=1
    ) == {
        "criteria": {"composition_reduced": dict(structure.composition.to_reduced_dict)}
    }

    docs = [{"structure": structure.as_dict(), "material_id": "mp-149"}]

    assert op.post_process(docs) == [
        {
            "material_id": "mp-149",
            "normalized_rms_displacement": 0,
            "max_distance_paired_sites": 0,
        }
    ]


def test_formula_auto_complete_query():
    op = FormulaAutoCompleteQuery()

    eles = ["Si", "O"]

    pipeline = [
        {
            "$search": {
                "index": "formula_autocomplete",
                "text": {"path": "formula_pretty", "query": ["SiO", "OSi"]},
            }
        },
        {
            "$project": {
                "_id": 0,
                "formula_pretty": 1,
                "elements": 1,
                "length": {"$strLenCP": "$formula_pretty"},
            }
        },
        {"$match": {"elements": {"$all": eles}, "length": {"$gte": 3}}},
        {"$limit": 10},
        {"$sort": {"length": 1}},
        {"$project": {"elements": 0, "length": 0}},
    ]

    assert op.query(formula="".join(eles), limit=10) == {"pipeline": pipeline}

    eles = ["Si"]

    pipeline = [
        {
            "$search": {
                "index": "formula_autocomplete",
                "text": {"path": "formula_pretty", "query": ["Si"]},
            }
        },
        {
            "$project": {
                "_id": 0,
                "formula_pretty": 1,
                "elements": 1,
                "length": {"$strLenCP": "$formula_pretty"},
            }
        },
        {"$match": {"elements": {"$all": eles}, "length": {"$gte": 2}}},
        {"$limit": 10},
        {"$sort": {"length": 1}},
        {"$project": {"elements": 0, "length": 0}},
    ]

    assert op.query(formula="".join(eles), limit=10) == {"pipeline": pipeline}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(formula="".join(eles), limit=10) == {"pipeline": pipeline}
