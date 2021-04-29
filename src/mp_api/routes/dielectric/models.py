from datetime import datetime
from monty.json import MontyDecoder

from emmet.core.polar import Dielectric

from pydantic import BaseModel, Field, validator


class DielectricDoc(BaseModel):
    """
    Model for a document containing dielectric data
    """

    dielectric: Dielectric = Field(
        None, description="Dielectric data",
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
