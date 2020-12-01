from pydantic import BaseModel, Field, validator
from datetime import datetime
from monty.json import MontyDecoder


class ChgcarDataDoc(BaseModel):
    fs_id: str = Field(
        None, description="Unique object ID for the charge density data."
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent update to the charge density data.",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the calculation producing the charge density data. \
            This comes in the form: mp-******",
    )

    data: dict = Field(None, description="Pymatgen CHGCAR object.")

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
