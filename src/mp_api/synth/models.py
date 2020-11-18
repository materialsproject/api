from pydantic import BaseModel, Field


class SynthDoc(BaseModel):
    """
    Model for a document containing synthesis description data
    """

    doi: str = Field(
        None,
        description="DOI of the journal article.",
    )

    formula: str = Field(
        None,
        description="Material formula.",
    )

    text: str = Field(
        None,
        description="Synthesis description.",
    )
