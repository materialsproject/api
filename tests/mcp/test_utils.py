import pytest

from mp_api.client.core.exceptions import MPRestError, MPRestWarning
from mp_api.mcp.utils import _NeedsMPClient


def test_mix_in():
    test_class = _NeedsMPClient()
    assert test_class.client.api_key is not None
    assert not test_class.client.use_document_model
    print(test_class.client.session.headers["user-agent"])
    assert test_class.client.session.headers["user-agent"].startswith("mp-mcp")

    with pytest.raises(MPRestError, match="Valid API keys are 32"):
        test_class.update_user_api_key(30 * "a")

    with pytest.warns(MPRestWarning, match="Ignoring `monty_decode`"):
        # Test that `use_document_model` is always enforced to be False, and user agent is included
        test_class = _NeedsMPClient(
            client_kwargs={
                "monty_decode": False,
                "use_document_model": True,
                "mute_progress_bars": True,
            }
        )
        assert not test_class.client.use_document_model
        assert test_class.client.mute_progress_bars
