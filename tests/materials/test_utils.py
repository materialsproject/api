from mp_api.materials.utils import formula_to_criteria


def test_formula_to_criteria():
    # Regular formula
    assert formula_to_criteria("Cr2O3") == {
        "composition_reduced.Cr": {"$gt": 1.98, "$lt": 2.02},
        "composition_reduced.O": {"$gt": 2.9699999999999998, "$lt": 3.0300000000000002},
        "nelements": 2,
    }
    # Add wildcard
    assert formula_to_criteria("Cr2*3") == {
        "composition_reduced.Cr": {"$gt": 1.98, "$lt": 2.02},
        "formula_anonymous": "A2B3",
    }
    # Anonymous element
    assert formula_to_criteria("A2B3") == {"formula_anonymous": "A2B3"}
