from typing import List

from pydantic import BaseModel, Field
from pymatgen.core import Composition

from mp_api.synthesis.models.materials import ExtractedMaterial
from mp_api.synthesis.models.operations import Operation
from mp_api.synthesis.models.reaction import ReactionFormula


class SynthesisRecipe(BaseModel):
    """
    Model for a document containing synthesis description data
    """

    # Basic facts about this recipe:
    doi: str = Field(
        ...,
        description="DOI of the journal article.",
    )
    paragraph_string: str = Field(
        "",
        description="The paragraph from which this recipe is extracted."
    )
    synthesis_type: str = Field(
        ...,
        description="Type of the synthesis recipe."
    )

    # Reaction related information:
    reaction_string: str = Field(
        ...,
        description="String representation of this recipe."
    )
    reaction: ReactionFormula = Field(
        ...,
        description="The balanced reaction formula."
    )

    target: ExtractedMaterial = Field(
        ...,
        description="The target material."
    )
    targets_string: List[Composition] = Field(
        ...,
        description="List of synthesized target material compositions."
    )

    precursors: List[ExtractedMaterial] = Field(
        ...,
        description="List of precursor materials."
    )

    operations: List[Operation] = Field(
        ...,
        description="List of operations used to synthesize this recipe."
    )
