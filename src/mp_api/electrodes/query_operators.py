from typing import Optional
from fastapi import Query
from pymatgen.core.periodic_table import ElementBase

from mp_api.core.query_operator import STORE_PARAMS, QueryOperator

from collections import defaultdict

# from mp_api.electrodes.models import WorkingIon


class VoltageStepQuery(QueryOperator):
    """
    Method to generate a query for ranges of voltage step data values
    """

    def query(
        self,
        delta_volume_max: Optional[float] = Query(
            None,
            description="Maximum value for the max Volume change in percent for a particular voltage step.",
        ),
        delta_volume_min: Optional[float] = Query(
            None,
            description="Minimum value for the max Volume change in percent for a particular voltage step.",
        ),
        average_voltage_max: Optional[float] = Query(
            None,
            description="Maximum value for the average voltage for a particular voltage step in V.",
        ),
        average_voltage_min: Optional[float] = Query(
            None,
            description="Minimum value for the average voltage for a particular voltage step in V.",
        ),
        max_voltage_max: Optional[float] = Query(
            None,
            description="Maximum value for the maximum voltage for a particular voltage step in V.",
        ),
        max_voltage_min: Optional[float] = Query(
            None,
            description="Minimum value for the maximum voltage for a particular voltage step in V.",
        ),
        min_voltage_max: Optional[float] = Query(
            None,
            description="Maximum value for the minimum voltage for a particular voltage step in V.",
        ),
        min_voltage_min: Optional[float] = Query(
            None,
            description="Minimum value for the minimum voltage for a particular voltage step in V.",
        ),
        capacity_grav_max: Optional[float] = Query(
            None, description="Maximum value for the gravimetric capacity in maH/g.",
        ),
        capacity_grav_min: Optional[float] = Query(
            None, description="Minimum value for the gravimetric capacity in maH/g.",
        ),
        capacity_vol_max: Optional[float] = Query(
            None, description="Maximum value for the volumetric capacity in maH/cc.",
        ),
        capacity_vol_min: Optional[float] = Query(
            None, description="Minimum value for the volumetric capacity in maH/cc.",
        ),
        energy_grav_max: Optional[float] = Query(
            None,
            description="Maximum value for the gravimetric energy (specific energy) in Wh/kg.",
        ),
        energy_grav_min: Optional[float] = Query(
            None,
            description="Minimum value for the gravimetric energy (specific energy) in Wh/kg.",
        ),
        energy_vol_max: Optional[float] = Query(
            None,
            description="Maximum value for the volumetric energy (energy_density) in Wh/l.",
        ),
        energy_vol_min: Optional[float] = Query(
            None,
            description="Minimum value for the volumetric energy (energy_density) in Wh/l.",
        ),
        fracA_charge_max: Optional[float] = Query(
            None,
            description="Maximum value for the atomic fraction of the working ion in the charged state.",
        ),
        fracA_charge_min: Optional[float] = Query(
            None,
            description="Minimum value for the atomic fraction of the working ion in the charged state.",
        ),
        fracA_discharge_max: Optional[float] = Query(
            None,
            description="Maximum value for the atomic fraction of the working ion in the discharged state.",
        ),
        fracA_discharge_min: Optional[float] = Query(
            None,
            description="Minimum value for the atomic fraction of the working ion in the discharged state.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "max_delta_volume": [delta_volume_min, delta_volume_max],
            "average_voltage": [average_voltage_min, average_voltage_max],
            "max_voltage": [max_voltage_min, max_voltage_max],
            "min_voltage": [min_voltage_min, min_voltage_max],
            "capacity_grav": [capacity_grav_min, capacity_grav_max],
            "capacity_vol": [capacity_vol_min, capacity_vol_max],
            "energy_grav": [energy_grav_min, energy_grav_max],
            "energy_vol": [energy_vol_min, energy_vol_max],
            "fracA_charge": [fracA_charge_min, fracA_charge_max],
            "fracA_discharge": [fracA_discharge_min, fracA_discharge_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class InsertionVoltageStepQuery(QueryOperator):
    """
    Method to generate a query for ranges of insertion voltage step data values
    """

    def query(
        self,
        stability_charge_max: Optional[float] = Query(
            None,
            description="The maximum value of the energy above hull of the charged material.",
        ),
        stability_charge_min: Optional[float] = Query(
            None,
            description="The minimum value of the energy above hull of the charged material.",
        ),
        stability_discharge_max: Optional[float] = Query(
            None,
            description="The maximum value of the energy above hull of the discharged material.",
        ),
        stability_discharge_min: Optional[float] = Query(
            None,
            description="The minimum value of the energy above hull of the discharged material.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "stability_charge": [stability_charge_min, stability_charge_max],
            "stability_discharge": [stability_discharge_min, stability_discharge_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class InsertionElectrodeQuery(QueryOperator):
    """
    Method to generate a query for ranges of insertion electrode data values
    """

    def query(
        self,
        working_ion: Optional[ElementBase] = Query(
            None, title="Element of the working ion"
        ),
        num_steps_max: Optional[float] = Query(
            None,
            description="The maximum value of the The number of distinct voltage steps from fully charge to \
                discharge based on the stable intermediate states.",
        ),
        num_steps_min: Optional[float] = Query(
            None,
            description="The minimum value of the The number of distinct voltage steps from fully charge to \
                discharge based on the stable intermediate states.",
        ),
        max_voltage_step_max: Optional[float] = Query(
            None,
            description="The maximum value of the maximum absolute difference in adjacent voltage steps.",
        ),
        max_voltage_step_min: Optional[float] = Query(
            None,
            description="The minimum value of maximum absolute difference in adjacent voltage steps.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "num_steps": [num_steps_min, num_steps_max],
            "max_voltage_step": [max_voltage_step_min, max_voltage_step_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        if working_ion:
            crit["working_ion"] = str(working_ion)

        return {"criteria": crit}
