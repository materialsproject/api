from pydantic import BaseModel, Field
from typing import List, Dict

class SynthesisDoc(BaseModel):
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

    highlights: List[Dict] = Field(
        None,
        description="Highlighted search terms when searching by keyword(s)."
    )
