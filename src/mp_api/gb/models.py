from typing import List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
from monty.json import MontyDecoder

from mp_api.materials.models.core import Lattice, PeriodicSite, Structure


class GBTypeEnum(Enum):
    """
    Grain boundary types
    """

    tilt = "tilt"
    twist = "twist"


class GrainBoundary(BaseModel):
    """
    Model for a pymatgen grain boundary object
    """

    charge: Optional[float] = Field(None, description="Total charge")
    lattice: Lattice = Field(None, description="Lattice for this structure")
    sites: List[PeriodicSite] = Field(
        None, description="List of sites in this structure"
    )
    init_cell: Structure = Field(
        None, description="Initial bulk structure to form the GB"
    )
    rotation_axis: List[int] = Field(None, description="Rotation axis")
    rotation_angle: float = Field(None, description="Rotation angle in degrees")
    gb_plane: List[int] = Field(None, description="Grain boundary plane")
    join_plane: List[int] = Field(
        None, description="Joining plane of the second grain",
    )
    vacuum_thickness: float = Field(
        None,
        description="The thickness of vacuum inserted between two grains of the GB",
    )
    ab_shit: List[float] = Field(
        None, description="The relative shift along a, b vectors"
    )
    oriented_unit_cell: Structure = Field(
        None, description="Oriented unit cell of the bulk init_cell"
    )

    class Config:
        extra = "allow"


class GBDoc(BaseModel):
    """
    Model for a document containing grain boundary data
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
