from typing import List
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
from monty.json import MontyDecoder

from pymatgen.analysis.gb.grain import GrainBoundary


class GBTypeEnum(Enum):
    """
    Grain boundary types
    """

    tilt = "tilt"
    twist = "twist"


class GrainBoundaryDoc(BaseModel):
    """
    Grain boundary energies, work of separation...
    """

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    sigma: int = Field(
        None, description="Sigma value of the boundary",
    )

    type: GBTypeEnum = Field(
        None, description="Grain boundary type",
    )

    rotation_axis: List[int] = Field(
        None, description="Rotation axis",
    )

    gb_plane: List[int] = Field(
        None, description="Grain boundary plane",
    )

    rotation_angle: float = Field(
        None, description="Rotation angle in degrees",
    )

    gb_energy: float = Field(
        None, description="Grain boundary energy in J/m^2",
    )

    initial_structure: GrainBoundary = Field(
        None, description="Initial grain boundary structure"
    )

    final_structure: GrainBoundary = Field(
        None, description="Final grain boundary structure"
    )

    pretty_formula: str = Field(None, description="Reduced formula of the material")

    w_sep: float = Field(None, description="Work of separation in J/m^2")

    cif: str = Field(None, description="CIF file of the structure")

    chemsys: str = Field(
        None, description="Dash-delimited string of elements in the material"
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
