from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn
from pymatgen.electronic_structure.core import OrbitalType

from mp_api.routes.electronic_structure.query_operators import (
    ESSummaryDataQuery,
    BSDataQuery,
    DOSDataQuery,
    ObjectQuery,
)
from mp_api.routes.electronic_structure.models.core import BSPathType, DOSProjectionType

from pymatgen.analysis.magnetism.analyzer import Ordering
from pymatgen.core.periodic_table import Element


def test_es_summary_query():
    op = ESSummaryDataQuery()

    assert op.query(
        magnetic_ordering=Ordering.FiM, is_gap_direct=True, is_metal=False
    ) == {
        "criteria": {
            "magnetic_ordering": "FiM",
            "is_gap_direct": True,
            "is_metal": False,
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(
            magnetic_ordering=Ordering.FiM, is_gap_direct=True, is_metal=False
        ) == {
            "criteria": {
                "magnetic_ordering": "FiM",
                "is_gap_direct": True,
                "is_metal": False,
            }
        }


def test_bs_data_query():
    op = BSDataQuery()

    q = op.query(
        path_type=BSPathType.setyawan_curtarolo,
        band_gap_min=0,
        band_gap_max=5,
        efermi_min=0,
        efermi_max=5,
        magnetic_ordering=Ordering.FM,
        is_gap_direct=True,
        is_metal=False,
    )

    fields = [
        "bandstructure.setyawan_curtarolo.band_gap",
        "bandstructure.setyawan_curtarolo.efermi",
    ]

    c = {field: {"$gte": 0, "$lte": 5} for field in fields}

    assert q == {
        "criteria": {
            "bandstructure.setyawan_curtarolo.magnetic_ordering": "FM",
            "bandstructure.setyawan_curtarolo.is_gap_direct": True,
            "bandstructure.setyawan_curtarolo.is_metal": False,
            **c,
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            path_type=BSPathType.setyawan_curtarolo,
            band_gap_min=0,
            band_gap_max=5,
            efermi_min=0,
            efermi_max=5,
            magnetic_ordering=Ordering.FM,
            is_gap_direct=True,
            is_metal=False,
        )
        c = {field: {"$gte": 0, "$lte": 5} for field in fields}

        assert q == {
            "criteria": {
                "bandstructure.setyawan_curtarolo.magnetic_ordering": "FM",
                "bandstructure.setyawan_curtarolo.is_gap_direct": True,
                "bandstructure.setyawan_curtarolo.is_metal": False,
                **c,
            }
        }


def test_dos_data_query():
    op = DOSDataQuery()

    proj_types = [
        DOSProjectionType.total,
        DOSProjectionType.elemental,
        DOSProjectionType.orbital,
    ]

    for proj_type in proj_types:
        q = op.query(
            projection_type=proj_type,
            spin="1",
            element=Element.Si if proj_type != DOSProjectionType.total else None,
            orbital=OrbitalType.s if proj_type != DOSProjectionType.total else None,
            band_gap_min=0,
            band_gap_max=5,
            efermi_min=0,
            efermi_max=5,
            magnetic_ordering=Ordering.FM,
        )

        if proj_type == DOSProjectionType.total:
            fields = [
                "dos.total.1.band_gap",
                "dos.total.1.efermi",
            ]
        elif proj_type == DOSProjectionType.elemental:
            fields = [
                "dos.elemental.Si.s.1.band_gap",
                "dos.elemental.Si.s.1.efermi",
            ]

        elif proj_type == DOSProjectionType.orbital:
            fields = [
                "dos.orbital.s.1.band_gap",
                "dos.orbital.s.1.efermi",
            ]

        c = {field: {"$gte": 0, "$lte": 5} for field in fields}

        assert q == {"criteria": {"dos.magnetic_ordering": "FM", **c}}

        with ScratchDir("."):
            dumpfn(op, "temp.json")
            new_op = loadfn("temp.json")
            q = new_op.query(
                projection_type=proj_type,
                spin="1",
                element=Element.Si if proj_type != DOSProjectionType.total else None,
                orbital=OrbitalType.s if proj_type != DOSProjectionType.total else None,
                band_gap_min=0,
                band_gap_max=5,
                efermi_min=0,
                efermi_max=5,
                magnetic_ordering=Ordering.FM,
            )
            c = {field: {"$gte": 0, "$lte": 5} for field in fields}

            assert q == {"criteria": {"dos.magnetic_ordering": "FM", **c}}


def test_object_query():
    op = ObjectQuery()

    assert op.query(task_id="mp-149") == {"criteria": {"task_id": "mp-149"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(task_id="mp-149") == {"criteria": {"task_id": "mp-149"}}
