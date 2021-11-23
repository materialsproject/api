"""
This script converts synthesis recipes data fetched directly
from Ceder Group Synthesis Mining team MongoDB into MP compatible
formats.
"""
import json
import os
import re

from pymatgen.core.composition import CompositionError, Composition
from pymongo import MongoClient


def convert_value(val):
    """Convert values in operation conditions dictionaries."""
    return {
        "min_value": float(val["min"]) if val["min"] is not None else None,
        "max_value": float(val["max"]) if val["max"] is not None else None,
        "values": [float(x) for x in val["values"]],
        "units": str(val["units"]),
    }


def convert_conditions(cond, op_type):
    """Convert conditions dictionaries."""
    return {
        "heating_temperature": [convert_value(x) for x in cond["temperature"]],
        "heating_time": [convert_value(x) for x in cond["time"]],
        "heating_atmosphere": [x.strip() for x in cond["environment"] if x.strip()]
        if op_type == "HeatingOperation"
        else [],
        "mixing_device": (
            cond["environment"][1].strip() if cond["environment"][1].strip() else None
        )
        if op_type == "MixingOperation"
        else None,
        "mixing_media": (
            cond["environment"][0].strip() if cond["environment"][0].strip() else None
        )
        if op_type == "MixingOperation"
        else None,
    }


all_posible_ops = set()


def convert_op(op):
    """Convert operation dictionaries."""
    all_posible_ops.add(op["type"])
    return {
        "type": op["type"],
        "token": op["string"],
        "conditions": convert_conditions(op["attributes"], op["type"]),
    }


def convert_mat_value(val):
    """Convert values specified in materials elements_vars."""
    return {
        "values": [float(x) for x in val["values"]],
        "min_value": float(val["min_value"]) if val["min_value"] is not None else None,
        "max_value": float(val["max_value"]) if val["max_value"] is not None else None,
    }


def convert_material(mat):
    """Convert materials dictionaries."""
    return {
        "material_string": str(mat["material_string"]),
        "material_name": str(mat["material_name"]),
        "material_formula": str(mat["material_formula"]),
        "phase": str(mat["phase"]) or None,
        "is_acronym": bool(mat["is_acronym"]),
        "composition": [
            {
                "formula": str(x["formula"]),
                "amount": str(x["amount"]),
                "elements": {str(y): str(z) for y, z in x["elements"].items()},
            }
            for x in mat["composition"]
        ],
        "amounts_vars": {
            x: convert_mat_value(y) for x, y in mat["amounts_vars"].items()
        },
        "elements_vars": {
            x: [str(z.strip()) for z in y if z.strip()]
            for x, y in mat["elements_vars"].items()
        },
        "additives": [str(x.strip()) for x in mat["additives"] if x.strip()],
        "oxygen_deficiency": str(mat["oxygen_deficiency"])
        if mat["oxygen_deficiency"]
        else None,
    }


def get_material_formula(mat):
    """Convert string material formulas into pymatgen Compositions."""
    formula = mat["material_formula"]
    formula = re.sub(r"·\d*H2O", "", formula)
    try:
        return Composition(formula)
    except (CompositionError, ValueError):
        q = None
        for comp in mat["composition"]:
            if q is None:
                q = Composition(
                    {x: float(y) for x, y in comp["elements"].items()}
                ) * float(comp["amount"])
            else:
                q += Composition(
                    {x: float(y) for x, y in comp["elements"].items()}
                ) * float(comp["amount"])
        return q


def target_comps(doc):
    """Find all target material formulas and convert them into Composition."""
    result = []
    for x in doc["targets_string"]:
        if not x.strip():
            continue
        try:
            result.append(Composition(x))
        except (CompositionError, ValueError):
            pass
    return result


def precursor_comps(doc):
    """Find all precursor material formulas and convert them into Composition."""
    result = []
    for x in doc["precursors"]:
        try:
            result.append(get_material_formula(x))
        except (CompositionError, ValueError):
            pass
    return result


def convert_one(doc):
    """Convert an entire synthesis recipe."""
    return {
        "doi": str(doc["doi"]),
        "paragraph_string": " ".join(doc["ext_paragraph"]),
        "synthesis_type": str(doc["synthesis_type"]),
        "reaction_string": str(doc["reaction_string"]),
        "reaction": {
            "left_side": [
                {"amount": str(x["amount"]), "material": str(x["material"])}
                for x in doc["reaction"]["left"]
            ],
            "right_side": [
                {"amount": str(x["amount"]), "material": str(x["material"])}
                for x in doc["reaction"]["right"]
            ],
        },
        "targets_formula": [x.formula for x in target_comps(doc)],
        "target": convert_material(doc["target"]),
        "targets_formula_s": [x.reduced_formula for x in target_comps(doc)],
        "precursors_formula_s": [x.reduced_formula for x in precursor_comps(doc)],
        "precursors_formula": [x.formula for x in precursor_comps(doc)],
        "precursors": [convert_material(x) for x in doc["precursors"]],
        "operations": [convert_op(x) for x in doc.get("operations", [])],
    }


def main():
    """
    Convert the Reactions_Solid_State/Reactions_Sol_Gel collection in
    Ceder Group database into a json file which can be imported into the MP database.
    """
    synpro_db = MongoClient(os.environ["SYNPRO_URI"]).SynPro

    synthesis_recipes = []

    for item in synpro_db.Reactions_Solid_State.find():
        synthesis_recipes.append(convert_one(item))
    for item in synpro_db.Reactions_Sol_Gel.find():
        synthesis_recipes.append(convert_one(item))

    with open("synthesis_recipes.json", "w") as f:
        json.dump(synthesis_recipes, f)

    print("All possible operation types", all_posible_ops)


if __name__ == "__main__":
    main()
