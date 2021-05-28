from typing import List
from pydantic import BaseModel, Field
from pymatgen.core.periodic_table import Element
from mp_api.routes.materials.models import Composition
from emmet.core.mpid import MPID


class MaterialProperty(BaseModel):
    """
    Class defining metadata that can be applied to a property of any material
    This metadata is used for search
    """

    # elements list for periodic table lookup
    elements: List[Element] = Field(
        None, description="List of elements in the material"
    )
    # Used to lookup formula components
    composition_reduced: Composition = Field(
        None,
        title="Reduced Composition",
        description="Simplified representation of the composition",
    )

    # Used to look up any anonymous formula
    formula_anonymous: str = Field(
        None,
        title="Anonymous Formula",
        description="Anonymized representation of the formula",
    )

    formula_pretty: str = Field(
        None, title="Pretty Formula", description="Human readable chemical formula"
    )

    material_id: str = Field(
        None,
        title="Material ID",
        description="The ID for the material this property document corresponds to",
    )


class FindStructure(BaseModel):
    """
    Class defining find structure return data
    """

    # elements list for periodic table lookup
    task_id: MPID = Field(
        None,
        description="The ID of this material, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )
    normalized_rms_displacement: float = Field(
        None,
        description="Volume normalized root-mean squared displacement between the structures",
    )
    max_distance_paired_sites: float = Field(
        None, description="Maximum distance between paired sites",
    )

