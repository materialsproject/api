from enum import Enum
from typing import List

from pydantic import BaseModel, Field, validator
from monty.json import MontyDecoder
from datetime import datetime


class MagnetismData(BaseModel):
    """
    Model for magnetic data within a magnetism doc
    """

    ordering: str = Field(
        None, description="Magnetic ordering.",
    )

    is_magnetic: bool = Field(
        None, description="Whether the material is magnetic.",
    )

    exchange_symmetry: int = Field(
        None, description="Exchange symmetry.",
    )

    num_magnetic_sites: int = Field(
        None, description="The number of magnetic sites.",
    )

    num_unique_magnetic_sites: int = Field(
        None, description="The number of unique magnetic sites.",
    )

    types_of_magnetic_species: List[str] = Field(
        None, description="Magnetic specie elements.",
    )

    magmoms: List[float] = Field(
        None, description="Magnetic moments for each site.",
    )

    total_magnetization: float = Field(
        None, description="Total magnetization in μB.",
    )

    total_magnetization_normalized_vol: float = Field(
        None, description="Total magnetization normalized by volume in μB/Å³.",
    )

    total_magnetization_normalized_formula_units: float = Field(
        None, description="Total magnetization normalized by formula unit in μB/f.u. .",
    )


class MagnetismDoc(BaseModel):
    """
    Magnetic ordering, total magnetizaiton, ...
    """

    task_id: str = Field(
        None,
        description="The ID of this material, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )

    magnetism: MagnetismData = Field(
        None, description="Magnetic data for the material",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
