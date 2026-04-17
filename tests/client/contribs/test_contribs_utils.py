"""Test MPContribs utilities."""

import hashlib
import orjson

from mp_api.client.contribs.utils import flatten_dict, get_md5, unflatten_dict


def test_un_flatten_dict_md5():
    dct = {
        "foo": {
            "bar": {
                "baz": 13.0,
                "bat": {
                    "fizz": True,
                    "whizz": False,
                },
            },
            "bin": None,
        }
    }

    for sep in (".", ":", ";"):
        flattened = flatten_dict(dct, separator=sep)
        assert flattened == {
            f"foo{sep}bar{sep}baz": 13.0,
            f"foo{sep}bar{sep}bat{sep}fizz": True,
            f"foo{sep}bar{sep}bat{sep}whizz": False,
            f"foo{sep}bin": None,
        }
        assert unflatten_dict(flattened, separator=sep) == dct

        assert (
            get_md5(flattened)
            == hashlib.md5(
                orjson.dumps({k: flattened[k] for k in sorted(flattened)})
            ).hexdigest()
        )
