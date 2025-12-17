
from mp_api.client.core.utils import LazyImport

def test_lazy_import_function():

    import_str = "json.dumps"
    lazy_func = LazyImport(import_str)
    assert lazy_func._module_name == "json"
    assert lazy_func._class_name == "dumps"
    assert str(lazy_func) == f"LazyImport of {import_str}"

    jsonables = [
        {"apple": "pineapple", "banana": "orange"},
        [1,2,3,4,5],
        [{"nothing": {"of": {"grand": "import"}}}]
    ]

    dumped = [
        lazy_func(jsonable) for jsonable in jsonables
    ]

    import json as _real_json
    
    assert lazy_func._imported == _real_json.dumps
    assert all(
        dumped[i] == _real_json.dumps(jsonable)
        for i, jsonable in enumerate(jsonables)
    )

def test_lazy_import_class():

    import_str = "pymatgen.core.Structure"
    lazy_class = LazyImport(import_str)
    assert lazy_class._module_name == "pymatgen.core"
    assert lazy_class._class_name == "Structure"
    assert str(lazy_class) == f"LazyImport of {import_str}"

    structure_str = """Si2
1.0
   3.3335729972004917    0.0000000000000000    1.9246389981090721
   1.1111909992801432    3.1429239987499362    1.9246389992542632
   0.0000000000000000    0.0000000000000000    3.8492780000000000
Si
2
direct
   0.8750000000000000    0.8750000000000000    0.8750000000000000 Si
   0.1250000000000000    0.1250000000000000    0.1250000000000000 Si"""
   
    # test construction from classmethod
    struct_from_str = lazy_class.from_str(structure_str, fmt = "poscar")
    # test re-init
    struct_from_init = lazy_class(struct_from_str.lattice,struct_from_str.species,struct_from_str.frac_coords)
    assert struct_from_str == struct_from_init

    from pymatgen.core.structure import Structure
    assert Structure.from_str(structure_str,fmt="poscar") == struct_from_str