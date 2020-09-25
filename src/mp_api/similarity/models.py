from typing import Dict, List

from pydantic import BaseModel, Field


class SimilarityDoc(BaseModel):
    """
    Model for a document containing structure similarity data
    """

    sim: List[Dict] = Field(
        None,
        description="List containing similar structure data for a given material.",
    )

    mid: str = Field(
        None,
        description="The Materials Project ID for the material. This comes in the form: mp-******",
    )

