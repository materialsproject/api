from pymatgen import Composition, DummySpecie
from typing import Dict


def formula_to_criteria(formula: str) -> Dict:
    """
    Santizes formula into a dictionary to search with wild cards

    Arguments:
        formula: a chemical formula with wildcards in it for unknown elements

    Returns:
        Mongo style search criteria for this formula
    """
    dummies = "ADEGJLMQRXZ"

    if "*" in formula:
        # Wild card in formula
        nstars = formula.count("*")

        formula_dummies = formula.replace("*", "{}").format(*dummies[:nstars])

        integer_formula = Composition(formula_dummies).get_integer_formula_and_factor()[
            0
        ]
        comp = Composition(integer_formula).reduced_composition
        crit = dict()
        crit["formula_anonymous"] = comp.anonymized_formula
        real_elts = [
            str(e)
            for e in comp.elements
            if not e.as_dict().get("element", "A") in dummies
        ]

        for el, n in comp.to_reduced_dict.items():
            if el in real_elts:
                crit[f"composition_reduced.{el}"] = n

        return crit

    elif "-" in formula:
        crit = {}
        eles = formula.split("-")
        chemsys = "-".join(sorted(eles))

        crit["chemsys"] = chemsys

        return crit

    elif any(isinstance(el, DummySpecie) for el in Composition(formula)):
        # Assume fully anonymized formula
        return {"formula_anonymous": Composition(formula).anonymized_formula}

    else:
        comp = Composition(formula)
        # Paranoia below about floating-point "equality"
        crit = {}
        crit["nelements"] = len(comp)
        for el, n in comp.to_reduced_dict.items():
            crit[f"composition_reduced.{el}"] = n

        return crit
