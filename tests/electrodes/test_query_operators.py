from mp_api.routes.electrodes.query_operators import (
    ElectrodeFormulaQuery,
    VoltageStepQuery,
    InsertionVoltageStepQuery,
    WorkingIonQuery,
)

from monty.tempfile import ScratchDir
from monty.serialization import loadfn, dumpfn


def test_electrode_formula_query():
    op = ElectrodeFormulaQuery()

    assert op.query(formula="BiFeO3") == {
        "criteria": {
            "framework.Bi": 1.0,
            "framework.Fe": 1.0,
            "framework.O": 3.0,
            "nelements": 3,
        }
    }

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        assert new_op.query(formula="BiFeO3") == {
            "criteria": {
                "framework.Bi": 1.0,
                "framework.Fe": 1.0,
                "framework.O": 3.0,
                "nelements": 3,
            }
        }


def test_voltage_step_query():
    op = VoltageStepQuery()

    q = op.query(
        delta_volume_min=0,
        delta_volume_max=5,
        average_voltage_min=0,
        average_voltage_max=5,
        max_voltage_min=0,
        max_voltage_max=5,
        min_voltage_min=0,
        min_voltage_max=5,
        capacity_grav_min=0,
        capacity_grav_max=5,
        capacity_vol_min=0,
        capacity_vol_max=5,
        energy_grav_min=0,
        energy_grav_max=5,
        energy_vol_min=0,
        energy_vol_max=5,
        fracA_charge_min=0,
        fracA_charge_max=5,
        fracA_discharge_min=0,
        fracA_discharge_max=5,
    )

    fields = [
        "max_delta_volume",
        "average_voltage",
        "max_voltage",
        "min_voltage",
        "capacity_grav",
        "capacity_vol",
        "energy_grav",
        "energy_vol",
        "fracA_charge",
        "fracA_discharge",
    ]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            delta_volume_min=0,
            delta_volume_max=5,
            average_voltage_min=0,
            average_voltage_max=5,
            max_voltage_min=0,
            max_voltage_max=5,
            min_voltage_min=0,
            min_voltage_max=5,
            capacity_grav_min=0,
            capacity_grav_max=5,
            capacity_vol_min=0,
            capacity_vol_max=5,
            energy_grav_min=0,
            energy_grav_max=5,
            energy_vol_min=0,
            energy_vol_max=5,
            fracA_charge_min=0,
            fracA_charge_max=5,
            fracA_discharge_min=0,
            fracA_discharge_max=5,
        )
        assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}


def test_insertion_voltage_step_query():
    op = InsertionVoltageStepQuery()

    q = op.query(
        stability_charge_min=0,
        stability_charge_max=5,
        stability_discharge_min=0,
        stability_discharge_max=5,
    )

    fields = [
        "stability_charge",
        "stability_discharge",
    ]

    assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(
            stability_charge_min=0,
            stability_charge_max=5,
            stability_discharge_min=0,
            stability_discharge_max=5,
        )
        assert q == {"criteria": {field: {"$gte": 0, "$lte": 5} for field in fields}}


def test_insertion_electrode_query():
    op = WorkingIonQuery()

    q = op.query(working_ion="Li",)

    assert q == {"criteria": {"working_ion": "Li"}}

    with ScratchDir("."):
        dumpfn(op, "temp.json")
        new_op = loadfn("temp.json")
        q = new_op.query(working_ion="Li",)

        assert q == {"criteria": {"working_ion": "Li"}}
