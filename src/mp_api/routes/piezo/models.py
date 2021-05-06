from typing import List
from datetime import datetime
from monty.json import MontyDecoder

from pydantic import BaseModel, Field, validator


class PiezoData(BaseModel):
    """
    Piezoelectric tensor and associated information.
    """

    total: List[List[float]] = Field(
        None,
        description="Total piezoelectric tensor in C/m²",
    )

    ionic: List[List[float]] = Field(
        None,
        description="Ionic contribution to piezoelectric tensor in C/m²",
    )

    static: List[List[float]] = Field(
        None,
        description="Electronic contribution to piezoelectric tensor in C/m²",
    )

    e_ij_max: float = Field(
        None,
        description="Piezoelectric modulus",
    )

    max_direction: List[float] = Field(
        None,
        description="Crystallographic direction",
    )


class PiezoDoc(BaseModel):
    """
    Model for a document containing piezoelectric data
    """

    piezo: PiezoData = Field(
        None,
        description="Piezoelectric data",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
