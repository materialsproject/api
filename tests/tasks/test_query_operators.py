import os
from mp_api.routes.tasks.query_operators import (
    MultipleTaskIDsQuery,
    TrajectoryQuery,
    DeprecationQuery,
)
from mp_api.core.settings import MAPISettings

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn
from json import load


def test_multiple_task_ids_query():
    op = MultipleTaskIDsQuery()

    assert op.query(task_ids=" mp-149, mp-13") == {
        "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert new_op.query(task_ids=" mp-149, mp-13") == {
            "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
        }


def test_trajectory_query():
    op = TrajectoryQuery()

    assert op.query(task_ids=" mp-149, mp-13") == {
        "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert new_op.query(task_ids=" mp-149, mp-13") == {
            "criteria": {"task_id": {"$in": ["mp-149", "mp-13"]}}
        }

    with open(os.path.join(MAPISettings().test_files, "tasks_Li_Fe_V.json")) as file:
        tasks = load(file)
    docs = op.post_process(tasks)
    assert docs[0]["trajectories"][0]["@class"] == "Trajectory"


def test_deprecation_query():
    op = DeprecationQuery()

    assert op.query(task_ids=" mp-149, mp-13") == {
        "criteria": {"deprecated_tasks": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert new_op.query(task_ids=" mp-149, mp-13") == {
            "criteria": {"deprecated_tasks": {"$in": ["mp-149", "mp-13"]}}
        }

    docs = [
        {"task_id": "mp-149", "deprecated_tasks": ["mp-149"]},
        {"task_id": "mp-13", "deprecated_tasks": ["mp-1234"]},
    ]
    r = op.post_process(docs)

    assert r[0] == {
        "task_id": "mp-149",
        "deprecated": True,
        "deprecation_reason": None,
    }

    assert r[1] == {
        "task_id": "mp-13",
        "deprecated": False,
        "deprecation_reason": None,
    }
