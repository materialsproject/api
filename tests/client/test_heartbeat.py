import requests
import pytest
from unittest.mock import patch, Mock

import mp_api.client.mprester

from .conftest import requires_api_key


@pytest.fixture
def mock_403():
    with patch("mp_api.client.mprester.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        yield mock_get


@requires_api_key
@pytest.mark.xfail(
    reason="Works in isolation, appear to be contamination from other test imports.",
    strict=False,
)
def test_heartbeat_403(mock_403):
    from mp_api.client.mprester import MPRester
    from mp_api.client.core import MPRestWarning

    with pytest.warns(MPRestWarning, match="heartbeat, check Materials Project status"):
        with MPRester() as mpr:
            # Ensure that client can still work if heartbeat is unreachable
            assert mpr.get_structure_by_material_id("mp-149") is not None
