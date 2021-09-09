from mp_api.routes.materials.utils import formula_to_criteria


def test_formula_to_criteria():
    # Regular formula
    assert formula_to_criteria("Cr2O3") == {
        "composition_reduced.Cr": 2.0,
        "composition_reduced.O": 3.0,
        "nelements": 2,
    }
    # Add wildcard
    assert formula_to_criteria("Cr2*3") == {
        "composition_reduced.Cr": 2.0,
        "formula_anonymous": "A2B3",
    }
    # Anonymous element
    assert formula_to_criteria("A2B3") == {"formula_anonymous": "A2B3"}

    # Chemsys
    assert formula_to_criteria("Si-O") == {"chemsys": "O-Si"}
    assert formula_to_criteria("Si-*") == {"elements": {"$all": ["Si"]}, "nelements": 2}
    assert formula_to_criteria("*-*-*") == {"nelements": 3}
