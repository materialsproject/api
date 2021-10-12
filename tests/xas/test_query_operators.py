from mp_api.routes.xas.query_operators import XASQuery, XASTaskIDQuery

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn

from emmet.core.xas import Edge, Type
from pymatgen.core.periodic_table import Element


def test_xas_operator():
    op = XASQuery()

    assert op.query(
        edge=Edge.K, spectrum_type=Type.XANES, absorbing_element=Element("Cu")
    ) == {
        "criteria": {"edge": "K", "absorbing_element": "Cu", "spectrum_type": "XANES"}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert new_op.query(
            edge=Edge.K, spectrum_type=Type.XANES, absorbing_element=Element("Cu")
        ) == {
            "criteria": {
                "edge": "K",
                "absorbing_element": "Cu",
                "spectrum_type": "XANES",
            }
        }


def test_xas_task_id_operator():
    op = XASTaskIDQuery()

    assert op.query(material_ids="mp-149, mp-13") == {
        "criteria": {"material_id": {"$in": ["mp-149", "mp-13"]}}
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")

        assert new_op.query(material_ids="mp-149, mp-13") == {
            "criteria": {"material_id": {"$in": ["mp-149", "mp-13"]}}
        }
