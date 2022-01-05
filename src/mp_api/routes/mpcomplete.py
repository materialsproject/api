from pydantic import Field
from pydantic.main import BaseModel
from pymatgen.core.structure import Structure
from enum import Enum


class MPCompleteDoc(BaseModel):
    """
    Defines data for MPComplete structure submissions
    """

    structure: Structure = Field(
        None,
        title="Submitted structure",
        description="Structure submitted by the user.",
    )

    public_name: str = Field(
        None, title="Public name", description="Public name of submitter.",
    )

    public_email: str = Field(
        None, title="Public email", description="Public email of submitter.",
    )


class MPCompleteDataStatus(Enum):
    """
    Submission status for MPComplete data
    """

    submitted = "SUBMITTED"
    pending = "PENDING"
    running = "RUNNING"
    error = "ERROR"
    complete = "COMPLETE"
