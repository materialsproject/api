from mp_api.routes.robocrys.query_operators import RoboTextSearchQuery
from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_robocrys_search_query():
    op = RoboTextSearchQuery()

    pipeline = [
        {
            "$search": {
                "index": "description",
                "regex": {
                    "query": ["cubic", "octahedra"],
                    "path": "description",
                    "allowAnalyzedField": True,
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "task_id": 1,
                "description": 1,
                "condensed_structure": 1,
                "last_updates": 1,
                "search_score": {"$meta": "searchScore"},
            }
        },
        {"$sort": {"search_score": -1}},
        {"$skip": 0},
        {"$limit": 10},
    ]

    assert op.query(keywords="cubic, octahedra", skip=0, limit=10) == {
        "pipeline": pipeline
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(keywords="cubic, octahedra", skip=0, limit=10) == {
            "pipeline": pipeline
        }

