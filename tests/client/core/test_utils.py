"""Test client core utilities."""

import pytest

from mp_api.client.core.exceptions import MPRestError, MPRestWarning
from mp_api.client.core.utils import LazyImport


def test_lazy_import_module():
    import_str = "typing"
    lazy_mod = LazyImport(import_str)
    assert lazy_mod._module_name == import_str
    assert lazy_mod._class_name is None
    assert lazy_mod.__repr__() == str(lazy_mod)
    lazy_any = lazy_mod.Any

    from typing import Any

    assert lazy_any == Any

    # Ensure failure to load raises error
    with pytest.raises(ImportError, match="Failed to import"):
        _ = LazyImport("tieping")._load()


def test_lazy_import_function():
    import_str = "json.dumps"
    lazy_func = LazyImport(import_str)
    assert lazy_func._module_name == "json"
    assert lazy_func._class_name == "dumps"
    assert str(lazy_func) == f"LazyImport of {import_str}"

    jsonables = [
        {"apple": "pineapple", "banana": "orange"},
        [1, 2, 3, 4, 5],
        [{"nothing": {"of": {"grand": "import"}}}],
    ]

    dumped = [lazy_func(jsonable) for jsonable in jsonables]

    import json as _real_json

    assert lazy_func._imported == _real_json.dumps
    assert all(
        dumped[i] == _real_json.dumps(jsonable) for i, jsonable in enumerate(jsonables)
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
    struct_from_str = lazy_class.from_str(structure_str, fmt="poscar")
    # test re-init
    struct_from_init = lazy_class(
        struct_from_str.lattice, struct_from_str.species, struct_from_str.frac_coords
    )
    assert struct_from_str == struct_from_init

    from pymatgen.core.structure import Structure

    assert Structure.from_str(structure_str, fmt="poscar") == struct_from_str

    # ensure copy yields an independent object
    lazy_copy = lazy_class.copy()
    lazy_class(
        struct_from_str.lattice, struct_from_str.species, struct_from_str.frac_coords
    )
    assert lazy_copy._obj is None
    assert lazy_class._obj == struct_from_str


def test_emmet_core_version_checks(monkeypatch: pytest.MonkeyPatch):
    ref_ver = (1, 2, "3rc5")
    ref_ver_str = ".".join(str(x) for x in ref_ver)

    import mp_api.client.core.utils

    monkeypatch.setattr(mp_api.client.core.utils, "_EMMET_CORE_VER", ref_ver_str)
    from mp_api.client.core.utils import _compare_emmet_ver

    assert _compare_emmet_ver(ref_ver_str, "==")

    next_ver = ".".join(str(x) for x in [ref_ver[0] + 1, *ref_ver[1:]])
    assert _compare_emmet_ver(next_ver, "<")
    assert _compare_emmet_ver(next_ver, "<=")

    prior_ver = ".".join(str(x) for x in [ref_ver[0], ref_ver[1] - 1, *ref_ver[2:]])
    assert _compare_emmet_ver(prior_ver, ">")
    assert _compare_emmet_ver(prior_ver, ">=")


def test_id_validation():
    from emmet.core.mpid import MPID, AlphaID

    from mp_api.client.core.utils import validate_ids
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    max_num_idxs = MAPI_CLIENT_SETTINGS.MAX_LIST_LENGTH

    with pytest.raises(MPRestError, match="too long"):
        _ = validate_ids([f"mp-{x}" for x in range(max_num_idxs + 1)])

    # For all legacy MPIDs, ensure these validate correctly
    assert all(
        isinstance(x, str) and MPID(x).string == x
        for x in validate_ids([f"mp-{y}" for y in range(max_num_idxs)])
    )

    # For all new AlphaIDs, ensure these validate correctly
    assert all(
        isinstance(x, str) and AlphaID(x).string == x
        for x in validate_ids([y + AlphaID._cut_point for y in range(max_num_idxs)])
    )


def test_api_key_validation(monkeypatch: pytest.MonkeyPatch):
    from mp_api.client.core.utils import validate_api_key
    import pymatgen.core

    # Ensure any user settings are ignored
    monkeypatch.setenv("MP_API_KEY", "")
    monkeypatch.setenv("PMG_MAPI_KEY", "")
    non_api_key_settings = {
        k: v for k, v in pymatgen.core.SETTINGS.items() if k != "PMG_MAPI_KEY"
    }
    monkeypatch.setattr(pymatgen.core, "SETTINGS", non_api_key_settings)

    with pytest.raises(MPRestError, match="32 characters"):
        validate_api_key("invalid_key")

    with pytest.warns(MPRestWarning, match="No API key found"):
        validate_api_key()

    junk_api_key = "a" * 32
    monkeypatch.setenv("MP_API_KEY", junk_api_key)
    assert validate_api_key() == junk_api_key
    assert validate_api_key(junk_api_key) == junk_api_key

    other_junk_api_key = "b" * 32
    monkeypatch.setattr(
        pymatgen.core,
        "SETTINGS",
        {**non_api_key_settings, "PMG_MAPI_KEY": other_junk_api_key},
    )
    # MP API environment variable takes precedence
    assert validate_api_key() == junk_api_key

    # Check that pymatgen API key is used
    monkeypatch.setenv("MP_API_KEY", "")
    assert validate_api_key() == other_junk_api_key
