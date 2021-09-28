from datetime import datetime
from monty.serialization import MontyDecoder

from pydantic import BaseModel, Field, validator


class MineralData(BaseModel):
    """
    Model for mineral data in the condensed structure robocrystallographer field
    """

    type: str = Field(
        None, description="Mineral type.",
    )


class CondensedStructureData(BaseModel):
    """
    Model for data in the condensed structure robocrystallographer field
    """

    formula: str = Field(
        None, description="Formula for the material.",
    )

    spg_symbol: str = Field(
        None, description="Space group symbol of the material.",
    )

    crystal_system: str = Field(
        None, description="Crystal system of the material.",
    )

    mineral: MineralData = Field(
        None, description="Matched mineral data for the material.",
    )

    dimensionality: int = Field(
        None, description="Dimensionality of the material.",
    )


class RobocrysDoc(BaseModel):
    """
    Structural features, mineral prototypes, dimensionality, ...
    """

    description: str = Field(
        None, description="Decription text from robocrytallographer.",
    )

    condensed_structure: CondensedStructureData = Field(
        None, description="Condensed structure data from robocrytallographer.",
    )

    material_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    last_updated: datetime = Field(
        None, description="Timestamp for the most recent calculation for this document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
