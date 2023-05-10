from __future__ import annotations

import os

import pytest

skip_if_no_api_key = pytest.mark.skipif(
    not os.getenv("MP_API_KEY"), reason="No API key found."
)
