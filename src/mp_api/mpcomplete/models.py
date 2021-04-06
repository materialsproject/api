from pydantic import BaseModel, Field
from pymatgen.core.structure import Structure


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

    comment: str = Field(
        None, title="Submission comment", description="User comment for submission.",
    )
