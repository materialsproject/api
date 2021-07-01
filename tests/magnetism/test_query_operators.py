from mp_api.routes.magnetism.query_operators import MagneticQuery

from pymatgen.analysis.magnetism import Ordering

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_magnetic_query():
    op = MagneticQuery()

    q = op.query(
        ordering=Ordering.FM,
        total_magnetization_min=0,
        total_magnetization_max=5,
        total_magnetization_normalized_vol_min=0,
        total_magnetization_normalized_vol_max=5,
        total_magnetization_normalized_formula_units_min=0,
        total_magnetization_normalized_formula_units_max=5,
        num_magnetic_sites_min=0,
        num_magnetic_sites_max=5,
        num_unique_magnetic_sites_min=0,
        num_unique_magnetic_sites_max=5,
    )

    fields = [
        "magnetism.total_magnetization",
        "magnetism.total_magnetization_normalized_vol",
        "magnetism.total_magnetization_normalized_formula_units",
        "magnetism.num_magnetic_sites",
        "magnetism.num_unique_magnetic_sites",
    ]

    c = {field: {"$gte": 0, "$lte": 5} for field in fields}

    assert q == {"criteria": {"magnetism.ordering": "FM", **c}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            ordering=Ordering.FM,
            total_magnetization_min=0,
            total_magnetization_max=5,
            total_magnetization_normalized_vol_min=0,
            total_magnetization_normalized_vol_max=5,
            total_magnetization_normalized_formula_units_min=0,
            total_magnetization_normalized_formula_units_max=5,
            num_magnetic_sites_min=0,
            num_magnetic_sites_max=5,
            num_unique_magnetic_sites_min=0,
            num_unique_magnetic_sites_max=5,
        )
        c = {field: {"$gte": 0, "$lte": 5} for field in fields}

        assert q == {"criteria": {"magnetism.ordering": "FM", **c}}
