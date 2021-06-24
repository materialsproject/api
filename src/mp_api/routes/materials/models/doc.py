from emmet.core.mpid import MPID
from pydantic import Field, BaseModel


class FindStructure(BaseModel):
    """
    Class defining find structure return data
    """

    material_id: MPID = Field(
        None,
        description="The ID of this material, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )
    normalized_rms_displacement: float = Field(
        None, description="Volume normalized root-mean squared displacement between the structures",
    )
    max_distance_paired_sites: float = Field(
        None, description="Maximum distance between paired sites",
    )


class FormulaAutocomplete(BaseModel):
    """
    Class defining formula autocomplete return data
    """

    formula_pretty: str = Field(
        None, description="Human readable chemical formula",
    )
