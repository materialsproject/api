"""Test client core utilities."""

from packaging.version import parse as parse_version
import pytest

from emmet.core.mpid import MPID, AlphaID


def test_emmet_core_version_checks(monkeypatch : pytest.MonkeyPatch):

    ref_ver = (1,2,"3rc5")
    ref_ver_str = ".".join(str(x) for x in ref_ver)

    import emmet.core
    monkeypatch.setattr(emmet.core,"__version__",ref_ver_str)
    from mp_api.client.core.utils import _compare_emmet_ver

    assert _compare_emmet_ver(ref_ver_str,"==")

    next_ver = ".".join(str(x) for x in [ref_ver[0] + 1,*ref_ver[1:]])
    assert _compare_emmet_ver(next_ver,"<")
    assert _compare_emmet_ver(next_ver,"<=")

    prior_ver = ".".join(str(x) for x in [ref_ver[0],ref_ver[1]-1,*ref_ver[2:]])
    assert _compare_emmet_ver(prior_ver,">")
    assert _compare_emmet_ver(prior_ver,">=")

def test_id_validation():

    from mp_api.client.core.utils import validate_ids
    from mp_api.client.core.settings import MAPIClientSettings

    max_num_idxs = MAPIClientSettings().MAX_LIST_LENGTH

    with pytest.raises(ValueError,match="too long"):
        _ = validate_ids(
            [f"mp-{x}" for x in range(max_num_idxs + 1)]
        )

    # For all legacy MPIDs, ensure these validate correctly
    assert all(
        isinstance(x,str) and MPID(x).string == x
        for x in validate_ids(
            [f"mp-{y}" for y in range(max_num_idxs)]
        )
    )

    # For all new AlphaIDs, ensure these validate correctly
    assert all(
        isinstance(x,str) and AlphaID(x).string == x
        for x in validate_ids(
            [y + AlphaID._cut_point for y in range(max_num_idxs)]
        )
    )