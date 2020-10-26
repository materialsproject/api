from typing import Dict, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from monty.json import MontyDecoder

from mp_api.materials.models.core import Composition, Element


class ComputedEntry(BaseModel):
    """
    Model for a computed entry
    """

    composition: Composition = Field(
        None, description="Full composition for this entry"
    )
    energy: float = Field(None, description="DFT total energy in eV")
    correction: float = Field(None, description="Energy correction in eV")
    energy_adjustments: List = Field(
        None,
        description="An optional list of EnergyAdjustment to be applied to the energy."
        " This is used to modify the energy for certain analyses."
        " Defaults to None.",
    )
    parameters: Dict = Field(
        None,
        description="Dictionary of extra parameters for the underlying calculation",
    )
    data: Dict = Field(None, description="Dictionary of extra data")
    entry_id: str = Field(None, description="Entry ID")

    class Config:
        extra = "allow"


class ExplanationDoc(BaseModel):
    """
    Model for explanation data in thermo doc
    """

    compatability: str = Field(None, description="Pymatgen compatability data used.")
    uncorrected_energy: float = Field(
        None, description="Uncorrected DFT total energy in eV"
    )
    corrected_energy: float = Field(
        None, description="Corrected DFT total energy in eV"
    )
    corrections: List[dict] = Field(
        None,
        description="List of corrections applied to obtain the corrected energy value.",
    )


class ThermoData(BaseModel):
    """
    Model for thermo data field in a thermo doc
    """

    energy: float = Field(
        None,
        description="Total energy in eV.",
    )

    energy_per_atom: float = Field(
        None,
        description="Total energy in eV/atom.",
    )

    formation_energy_per_atom: float = Field(
        None,
        description="Formation energy in eV/atom.",
    )

    e_above_hull: float = Field(
        None,
        description="Energy above the hull in eV/atom.",
    )

    is_stable: bool = Field(
        None,
        description="Whether the material is stable.",
    )

    eq_reaction_e: bool = Field(
        None,
        description="Equilibrium reaction energy in eV/atom.",
    )

    entry: ComputedEntry = Field(
        None,
        description="Computed entry for the material.",
    )

    explanation: ExplanationDoc = Field(
        None,
        description="Thermo entry explanation data.",
    )


class ThermoDoc(BaseModel):
    """
    Model for a document containing thermo data
    """

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    thermo: ThermoData = Field(
        None,
        description="Thermo data for the material.",
    )

    chemsys: str = Field(
        None,
        description="Dash-delimited string of elements in the material.",
    )

    nelements: int = Field(
        None,
        description="Number of elements in the material.",
    )

    elements: List[Element] = Field(
        None, description="List of elements in the material"
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
