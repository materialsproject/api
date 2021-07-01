from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn

from mp_api.routes.search.query_operators import (
    HasPropsQuery,
    MaterialIDsSearchQuery,
    SearchIsStableQuery,
    SearchMagneticQuery,
    SearchIsTheoreticalQuery,
    SearchStatsQuery,
    SearchESQuery,
)

from mp_api.routes.search.models import SearchStats

from pymatgen.analysis.magnetism import Ordering
from emmet.core.search import SearchDoc


def test_has_props_query():
    op = HasPropsQuery()

    assert op.query(has_props="electronic_structure, thermo") == {
        "criteria": {"has_props": {"$all": ["electronic_structure", "thermo"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(has_props="electronic_structure, thermo") == {
            "criteria": {"has_props": {"$all": ["electronic_structure", "thermo"]}}
        }


def test_material_ids_query():
    op = MaterialIDsSearchQuery()

    assert op.query(material_ids="mp-149, mp-13") == {
        "criteria": {"material_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(material_ids="mp-149, mp-13") == {
            "criteria": {"material_id": {"$in": ["mp-149", "mp-13"]}}
        }


def test_is_stable_query():
    op = SearchIsStableQuery()

    assert op.query(is_stable=True) == {"criteria": {"is_stable": True}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(is_stable=True) == {"criteria": {"is_stable": True}}


def test_magnetic_query():
    op = SearchMagneticQuery()

    assert op.query(ordering=Ordering.FiM) == {"criteria": {"ordering": "FiM"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(ordering=Ordering.FiM) == {"criteria": {"ordering": "FiM"}}


def test_is_theoretical_query():
    op = SearchIsTheoreticalQuery()

    assert op.query(theoretical=False) == {"criteria": {"theoretical": False}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(theoretical=False) == {"criteria": {"theoretical": False}}


def test_search_stats_query():
    op = SearchStatsQuery(SearchDoc)

    pipeline = [
        {"$match": {"band_gap": {"$gte": 0, "$lte": 5}}},
        {"$sample": {"size": 10}},
        {"$project": {"band_gap": 1, "_id": 0}},
    ]

    assert op.query(
        field="band_gap", num_samples=10, min_val=0, max_val=5, num_points=100
    ) == {"pipeline": pipeline}

    docs = [{"band_gap": 1}, {"band_gap": 2}, {"band_gap": 3}]

    assert isinstance(op.post_process(docs)[0], SearchStats)


def test_search_es_query():
    op = SearchESQuery()

    assert op.query(is_gap_direct=False, is_metal=False) == {
        "criteria": {"is_gap_direct": False, "is_metal": False}
    }
