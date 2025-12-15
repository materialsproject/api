"""Test client core utilities."""

import pytest

from emmet.core.mpid import MPID, AlphaID

from mp_api.client.core.utils import validate_ids
from mp_api.client.core.settings import MAPIClientSettings

def test_id_validation():
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