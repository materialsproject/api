from pydantic import Field
from pymatgen.core.structure import Structure
from maggma.api.models import UserSubmissionDataModel


class MPCompleteDoc(UserSubmissionDataModel):
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
