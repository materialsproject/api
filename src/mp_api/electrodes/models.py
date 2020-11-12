from monty.json import MontyDecoder


""" Core definition of an Electrode Document """
from typing import List, Dict, ClassVar
from datetime import datetime

from pydantic import BaseModel, Field, validator
from mp_api.materials.models import Structure, Composition, CrystalSystem


class VoltageStep(BaseModel):
    """
    Data for individual voltage steps.
    Note: Each voltage step is represented as a sub_electrode (ConversionElectrode/InsertionElectrode)
        object to gain access to some basic statistics about the voltage step
    """

    max_delta_volume: str = Field(
        None,
        description="Volume changes in % for a particular voltage step using: " 
                    "max(charge, discharge) / min(charge, discharge) - 1"
    )

    average_voltage: float = Field(
        None,
        description="The average voltage in V for a particular voltage step.",
    )

    max_voltage: float = Field(
        None,
        description="The max voltage in V for a particular voltage step.",
    )

    min_voltage: float = Field(
        None,
        description="The min voltage in V for a particular voltage step.",
    )

    capacity_grav: float = Field(
        None, description="Gravimetric capacity in mAh/g."
    )

    capacity_vol: float = Field(
        None, description="Volumetric capacity in mAh/cc."
    )

    energy_grav: float = Field(
        None, description="Gravimetric energy (Specific energy) in Wh/kg."
    )

    energy_vol: float = Field(
        None, description="Volumetric energy (Eneryg Density) in Wh/l."
    )

    fracA_charge: float = Field(
        None, description=""
    )

    fracA_discharge: float = Field(
        None, description=""
    )

class ConverionVoltageStep(VoltageStep):
    """
    Features specific to conversion electrode
    """
    reactions: float = Field(
        None, description=""
    )

class InsertionVoltageStep(VoltageStep):
    """
    Features specific to insertion electrode
    """
    framework: float = Field(
        None, description=""
    )

    stability_charge: float = Field(
        None, description=""
    )

    stability_discharge: float = Field(
        None, description=""
    )

class InsertionElectrode(InsertionVoltageStep):

    battery_id: str = Field(None, description="The id for this battery document.")

    framework: Composition = Field(
        None,
        description="Framework structure (take the structure with the most working ion"
            "Then remove the working ions to get a host structure)",
    )

    voltage_pairs: List = Field(
        None, description="Returns all the Voltage Steps",
    )

    working_ion: str = Field(
        None, description="The working ion as an Element object",
    )

    num_steps: float = Field(
        None,
        description="The number of distinct voltage steps in from fully charge to "
        "discharge based on the stable intermediate states",
    )

    max_voltage_step: float = Field(
        None, description="Maximum absolute difference in adjacent voltage steps"
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)