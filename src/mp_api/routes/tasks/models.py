from datetime import datetime
from enum import Enum
from json import decoder
from typing import List, Dict

from monty.json import MontyDecoder
from pydantic import BaseModel, Field, validator

from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import Element
from pymatgen.io.vasp import Incar, Poscar, Kpoints
from pymatgen.core.trajectory import Trajectory

monty_decoder = MontyDecoder()


class TaskType(str, Enum):
    """
    The type of calculation
    """

    EMPTY = ""
    GGA_NSCF_Line = "GGA NSCF Line"
    GGA_NSCF_Uniform = "GGA NSCF Uniform"
    GGA_Static = "GGA Static"
    GGA_Structure_Optimization = "GGA Structure Optimization"
    GGA_U_NSCF_Line = "GGA+U NSCF Line"
    GGA_U_NSCF_Uniform = "GGA+U NSCF Uniform"
    GGA_U_Static = "GGA+U Static"
    GGA_U_Structure_Optimization = "GGA+U Structure Optimization"


class Potcar(BaseModel):
    functional: str = Field(None, description="Functional type use in the calculation.")

    symbols: List[str] = Field(
        None, description="List of VASP potcar symbols used in the calculation."
    )


class OrigInputs(BaseModel):
    incar: Incar = Field(
        None, description="Pymatgen object representing the INCAR file",
    )

    poscar: Poscar = Field(
        None, description="Pymatgen object representing the POSCAR file",
    )

    kpoints: Kpoints = Field(
        None, description="Pymatgen object representing the KPOINTS file",
    )

    potcar: Potcar = Field(
        None, description="Pymatgen object representing the POTCAR file",
    )


class OutputDoc(BaseModel):
    structure: Structure = Field(
        None,
        title="Output Structure",
        description="Output Structure from the VASP calculation",
    )

    density: float = Field(..., description="Density of in units of g/cc")
    energy: float = Field(..., description="Total Energy in units of eV")
    forces: List[List[float]] = Field(
        None, description="The force on each atom in units of eV/AA"
    )
    stress: List[List[float]] = Field(
        None, description="The stress on the cell in units of kB"
    )


class InputDoc(BaseModel):
    structure: Structure = Field(
        None,
        title="Input Structure",
        description="Output Structure from the VASP calculation",
    )


class CalcsReversedDoc(BaseModel):
    output: dict = Field(
        None,
        title="Calcs Reversed Output",
        description="Detailed output data for VASP calculations in calcs reversed.",
    )
    input: dict = Field(
        None,
        title="Calcs Reversed Input",
        description="Detailed input data for VASP calculations in calcs reversed.",
    )
    vasp_version: str = Field(
        None,
        title="Vasp Version",
        description="Version of VASP used for the calculation.",
    )


class CustodianDoc(BaseModel):
    corrections: List[dict] = Field(
        None,
        title="Custodian Corrections",
        description="List of custodian correction data for calculation.",
    )
    job: dict = Field(
        None, title="Cusotodian Job Data", description="Job data logged by custodian.",
    )


class AnalysisDoc(BaseModel):
    delta_volume: float = Field(
        None, title="Volume Change", description="Volume change for the calculation.",
    )
    delta_volume_percent: float = Field(
        None,
        title="Volume Change Percent",
        description="Percent volume change for the calculation.",
    )
    max_force: float = Field(
        None,
        title="Max Force",
        description="Maximum force on any atom at the end of the calculation.",
    )

    warnings: List[str] = Field(
        None,
        title="Calculation Warnings",
        description="Warnings issued after analysis.",
    )

    errors: List[str] = Field(
        None, title="Calculation Errors", description="Errors issued after analysis.",
    )


class TaskDoc(BaseModel):
    """
    Calculation-level details about VASP calculations that power Materials Project.
    """

    tags: List[str] = Field(
        None, title="tag", description="Metadata tagged to a given task"
    )

    calcs_reversed: List[CalcsReversedDoc] = Field(
        None,
        title="Calcs reversed data",
        description="Detailed data for each VASP calculation contributing to the task document.",
    )

    task_type: TaskType = Field(None, description="The type of calculation")

    task_id: str = Field(
        None,
        description="The ID of this calculation, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )

    # Structure metadata
    nsites: int = Field(None, description="Total number of sites in the structure")
    elements: List[Element] = Field(
        None, description="List of elements in the material"
    )
    nelements: int = Field(None, title="Number of Elements")
    composition: Composition = Field(
        None, description="Full composition for the material"
    )
    composition_reduced: Composition = Field(
        None,
        title="Reduced Composition",
        description="Simplified representation of the composition",
    )
    formula_pretty: str = Field(
        None,
        title="Pretty Formula",
        description="Cleaned representation of the formula",
    )
    formula_anonymous: str = Field(
        None,
        title="Anonymous Formula",
        description="Anonymized representation of the formula",
    )
    chemsys: str = Field(
        None,
        title="Chemical System",
        description="dash-delimited string of elements in the material",
    )

    orig_inputs: OrigInputs = Field(
        None,
        description="The exact set of input parameters used to generate the current task document.",
    )

    input: InputDoc = Field(
        None,
        description="The input structure used to generate the current task document.",
    )

    output: OutputDoc = Field(
        None,
        description="The exact set of output parameters used to generate the current task document.",
    )

    custodian: List[CustodianDoc] = Field(
        None,
        title="Calcs reversed data",
        description="Detailed custodian data for each VASP calculation contributing to the task document.",
    )

    analysis: AnalysisDoc = Field(
        None,
        title="Calculation Analysis",
        description="Some analysis of calculation data after collection.",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this task document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return monty_decoder.process_decoded(v)


class TrajectoryDoc(BaseModel):
    """
    Model for task trajectory data
    """

    task_id: str = Field(
        None,
        description="The ID of this calculation, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )

    trajectories: List[Trajectory] = Field(
        None,
        title="Trajectory data for calculations associated with a task doc",
        description="Trajectory data for calculations associated with a task doc",
    )


class DeprecationDoc(BaseModel):
    """
    Model for task deprecation data
    """

    task_id: str = Field(
        None,
        description="The ID of this calculation, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )

    deprecated: bool = Field(
        None, description="Whether the ID corresponds to a deprecated calculation.",
    )

    deprecation_reason: str = Field(
        None, description="Reason for deprecation.",
    )
