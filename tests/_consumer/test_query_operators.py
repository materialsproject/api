from mp_api.routes._consumer.query_operator import (
    UserSettingsGetQuery,
    UserSettingsPostQuery,
)

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_user_settings_post_query():
    op = UserSettingsPostQuery()

    assert op.query(consumer_id="test", settings={"test": "test", "test2": 10}) == {
        "criteria": {"consumer_id": "test", "settings": {"test": "test", "test2": 10}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(
            consumer_id="test", settings={"test": "test", "test2": 10}
        ) == {
            "criteria": {
                "consumer_id": "test",
                "settings": {"test": "test", "test2": 10},
            }
        }

    docs = [{"consumer_id": "test", "settings": {"test": "test", "test2": 10}}]
    assert op.post_process(docs) == docs


def test_user_settings_get_query():
    op = UserSettingsGetQuery()

    assert op.query(consumer_id="test") == {"criteria": {"consumer_id": "test"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(consumer_id="test") == {"criteria": {"consumer_id": "test"}}
