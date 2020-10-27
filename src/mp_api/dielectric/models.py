from typing import List
from datetime import datetime
from monty.json import MontyDecoder

from pydantic import BaseModel, Field, validator


class DielectricData(BaseModel):
    """
    Model for dielectric data in dielectric document
    """

    total: List[List[float]] = Field(
        None,
        description="Total dielectric tensor",
    )

    ionic: List[List[float]] = Field(
        None,
        description="Ionic contribution to dielectric tensor",
    )

    static: List[List[float]] = Field(
        None,
        description="Electronic contribution to dielectric tensor",
    )

    e_total: float = Field(
        None,
        description="Total dielectric constant",
    )

    e_ionic: float = Field(
        None,
        description="Ionic contributio to dielectric constant",
    )

    e_static: float = Field(
        None,
        description="Electronic contribution to dielectric constant",
    )

    n: float = Field(
        None,
        description="Refractive index",
    )


class DielectricDoc(BaseModel):
    """
    Model for a document containing dielectric data
    """

    dielectric: DielectricData = Field(
        None,
        description="Dielectric data",
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
