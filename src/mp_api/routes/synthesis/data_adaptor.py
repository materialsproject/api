"""
This script converts synthesis recipes data fetched directly
from the public repo of synthesis recipes
(https://github.com/CederGroupHub/text-mined-synthesis_public)
into MP compatible formats.
"""
import json
import sys

from pymatgen.core import Composition
from pymatgen.core.composition import CompositionError


def string2comp(x):
    """Convert string material formulas into pymatgen Compositions."""
    # TODO: if a material contains multiple parts, this function
    #  only takes the first part. This is not the optimal solution,
    #  and should be resolved in the future.
    formula = x.split('·')

    # return reduce(add, [Composition(x) for x in formula])
    return Composition(formula[0])


def convert_recipe(recipe):
    """Convert an entire synthesis recipe."""
    targets_string = recipe['targets_string']
    try:
        target_comps = [string2comp(x) for x in targets_string]
    except (CompositionError, ValueError):
        print('Cannot process materials: ', targets_string)
        raise

    recipe['targets_formula'] = [x.formula for x in target_comps]
    recipe['targets_formula_s'] = [x.reduced_formula for x in target_comps]
    del recipe['targets_string']

    recipe['precursors_formula'] = []
    recipe['precursors_formula_s'] = []
    for precursor in recipe['precursors']:
        try:
            comp = string2comp(precursor['material_formula'])
        except (CompositionError, ValueError):
            print('Cannot process precursor material: ', precursor['material_formula'])
            continue
        recipe['precursors_formula'].append(comp.formula)
        recipe['precursors_formula_s'].append(comp.reduced_formula)

    return recipe


def convert_json_public_repo(src_json, dst_json):
    """
    Convert the public synthesis recipes dataset (in a json file)
    into a format as json file which can be imported into the MP database.
    """
    with open(src_json) as f:
        data = json.load(f)
        recipes = data['reactions']

        print('Loaded %s recipes, version %s' % (len(recipes), data['release_date']))

    converted = []
    for recipe in recipes:
        try:
            convert_recipe(recipe)
            converted.append(recipe)
        except (CompositionError, ValueError, IndexError):
            pass

    print('Converted %d recipes' % (len(converted),))
    with open(dst_json, 'w') as f:
        json.dump(converted, f)


if __name__ == '__main__':
    convert_json_public_repo(sys.argv[1], sys.argv[2])
