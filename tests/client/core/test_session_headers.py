"""Shared-session header handling, without network access.

Applications (e.g. a web server) pass one `requests.Session` to every rester
in a process. Per-client credentials and consumer headers must then travel
with each request, never be written onto that shared session.
"""

from unittest.mock import MagicMock

import pytest
import requests

import mp_api.client.core.client as client_module
from mp_api.client.core.client import BaseRester

KEY_A = "a" * 32
KEY_B = "b" * 32


@pytest.fixture(autouse=True)
def _no_heartbeat(monkeypatch):
    monkeypatch.setattr(
        BaseRester, "_get_heartbeat_info", staticmethod(lambda endpoint: ("v", []))
    )


@pytest.fixture
def dev_env(monkeypatch):
    monkeypatch.setattr(client_module, "is_dev_env", lambda: True)


@pytest.fixture
def prod_env(monkeypatch):
    monkeypatch.setattr(client_module, "is_dev_env", lambda: False)


def test_dev_key_not_written_to_shared_session(dev_env):
    session = requests.Session()
    before = dict(session.headers)

    a = BaseRester(api_key=KEY_A, session=session)
    b = BaseRester(api_key=KEY_B, session=session)

    assert dict(session.headers) == before
    assert "x-api-key" not in session.headers
    assert a.headers["x-api-key"] == KEY_A
    assert b.headers["x-api-key"] == KEY_B


def test_dev_key_on_own_session(dev_env):
    # Without a caller session, the rester's own session still carries the key
    rester = BaseRester(api_key=KEY_A)
    assert rester.session.headers["x-api-key"] == KEY_A


def test_prod_headers_not_given_dev_key(prod_env):
    consumer = {"X-Consumer-Id": "abc"}
    rester = BaseRester(api_key=KEY_A, session=requests.Session(), headers=consumer)
    assert rester.headers == consumer
    # the caller's dict isn't mutated
    assert consumer == {"X-Consumer-Id": "abc"}


def test_caller_headers_not_mutated(dev_env):
    headers = {"X-Consumer-Id": "abc"}
    BaseRester(api_key=KEY_A, session=requests.Session(), headers=headers)
    assert headers == {"X-Consumer-Id": "abc"}


@pytest.mark.parametrize("method", ["post", "patch"])
def test_write_requests_forward_headers(prod_env, method):
    session = MagicMock(spec=requests.Session)
    response = MagicMock(status_code=200, text='{"data": []}')
    getattr(session, method).return_value = response

    consumer = {"X-Consumer-Id": "abc", "X-Consumer-Custom-Id": KEY_A}
    rester = BaseRester(api_key=KEY_A, session=session, headers=consumer)
    getattr(rester, f"_{method}_resource")(body={"x": 1}, use_document_model=False)

    kwargs = getattr(session, method).call_args.kwargs
    assert kwargs["headers"] == consumer
