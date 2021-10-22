from mp_api.routes._general_store.query_operator import (
    GeneralStoreGetQuery,
    GeneralStorePostQuery,
)

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_user_settings_post_query():
    op = GeneralStorePostQuery()

    assert op.query(
        kind="test", meta={"test": "test", "test2": 10}, markdown="test"
    ) == {
        "criteria": {
            "kind": "test",
            "meta": {"test": "test", "test2": 10},
            "markdown": "test",
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(
            kind="test", meta={"test": "test", "test2": 10}, markdown="test"
        ) == {
            "criteria": {
                "kind": "test",
                "meta": {"test": "test", "test2": 10},
                "markdown": "test",
            }
        }

    docs = [{"kind": "test", "meta": {"test": "test", "test2": 10}, "markdown": "test"}]
    assert op.post_process(docs) == docs


def test_user_settings_get_query():
    op = GeneralStoreGetQuery()

    assert op.query(kind="test") == {"criteria": {"kind": "test"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(kind="test") == {"criteria": {"kind": "test"}}
