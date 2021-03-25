from monty.json import MontyDecoder
from pymatgen.core.periodic_table import Element
from pymatgen.core import Structure
from typing import Dict, List, Union
from datetime import datetime

from pydantic import BaseModel, Field, validator
from mp_api.materials.models import Composition

from pymatgen.apps.battery.insertion_battery import InsertionElectrode


class VoltageStep(BaseModel):
    """
    Data for individual voltage steps.
    Note: Each voltage step is represented as a sub_electrode (ConversionElectrode/InsertionElectrode)
        object to gain access to some basic statistics about the voltage step
    """

    max_delta_volume: str = Field(
        None,
        description="Volume changes in % for a particular voltage step using: "
        "max(charge, discharge) / min(charge, discharge) - 1",
    )

    average_voltage: float = Field(
        None, description="The average voltage in V for a particular voltage step.",
    )

    min_voltage: float = Field(
        None, description="The min voltage in V for a particular voltage step.",
    )

    capacity_grav: float = Field(None, description="Gravimetric capacity in mAh/g.")

    capacity_vol: float = Field(None, description="Volumetric capacity in mAh/cc.")

    energy_grav: float = Field(
        None, description="Gravimetric energy (Specific energy) in Wh/kg."
    )

    energy_vol: float = Field(
        None, description="Volumetric energy (Energy Density) in Wh/l."
    )

    fracA_charge: float = Field(
        None, description="Atomic fraction of the working ion in the charged state."
    )
    fracA_discharge: float = Field(
        None, description="Atomic fraction of the working ion in the discharged state."
    )


class InsertionVoltageStep(VoltageStep):
    """
    Features specific to insertion electrode
    """

    formula_charge: str = Field(
        None, description="The chemical formula of the charged material."
    )

    formula_discharge: str = Field(
        None, description="The chemical formula of the discharged material."
    )

    stability_charge: float = Field(
        None, description="The energy above hull of the charged material."
    )

    stability_discharge: float = Field(
        None, description="The energy above hull of the discharged material."
    )

    id_charge: Union[str] = Field(
        None, description="The material-id of the charged structure."
    )

    id_discharge: Union[str] = Field(
        None, description="The material-id of the discharged structure."
    )


class InsertionElectrodeDoc(InsertionVoltageStep):

    battery_id: str = Field(None, description="The id for this battery document.")

    framework_formula: str = Field(
        None, description="The id for this battery document."
    )

    host_structure: Structure = Field(
        None, description="Host structure (structure without the working ion)",
    )

    adj_pairs: List[InsertionVoltageStep] = Field(
        None,
        description="Returns all the Voltage Steps",
    )

    working_ion: Element = Field(
        None,
        description="The working ion as an Element object",
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

    framework: Composition = Field(
        None, description="The chemical compositions of the host framework",
    )

    material_ids: List[str] = Field(
        None,
        description="The ids of all structures that matched to the present host lattice, regardless of stability. "
        "The stable entries can be found in the adjacent pairs.",
    )

    elements: List[Element] = Field(
        None, description="The atomic species contained in this electrode.",
    )

    chemsys: str = Field(
        None,
        description="The chemical system this electrode belongs to. "
        "Note: The conversion electrode can be calculated on this chemical system",
    )

    electrode_object: InsertionElectrode = Field(
        None, description="Returns InsertionElectrode object",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)


class ConversionVoltageStep(VoltageStep):
    """
    Features specific to conversion electrode
    """

    reactions: Dict = Field(
        None, description="The reaction the characterizes that particular voltage step."
    )


class ConversionElectrode(ConversionVoltageStep):

    battery_id: str = Field(None, description="The id for this battery document.")

    electrode_object: InsertionElectrode = Field(
        None, description="Returns InsertionElectrode object",
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
