"""Test client core utilities."""

from packaging.version import parse as parse_version
import pytest

from mp_api.client.core.exceptions import MPRestError


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
    from mp_api.client.core.settings import MAPIClientSettings

    max_num_idxs = MAPIClientSettings().MAX_LIST_LENGTH

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

    with pytest.raises(MPRestError, match="Please obtain a valid"):
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
