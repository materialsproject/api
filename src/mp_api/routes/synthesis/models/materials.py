from typing import List, Dict, Optional

from pydantic import BaseModel, Field

__all__ = ["Component", "ExtractedMaterial"]


class Component(BaseModel):
    formula: str = Field(..., description="Formula of this component.")
    amount: str = Field(..., description="Amount of this component.")
    elements: Dict[str, str] = Field(
        ..., description="Amount of each chemical elements in this component."
    )


class Values(BaseModel):
    values: List[float] = Field(None, description="List of values.")
    min_value: Optional[float] = Field(None, description="Minimal value.")
    max_value: Optional[float] = Field(None, description="Maximal value.")


class ExtractedMaterial(BaseModel):
    """
    Model for a material extracted from the literature
    """

    material_string: str = Field(
        ..., description="String of the material as written in paper."
    )
    material_formula: str = Field(
        ..., description="Normalized formula of the material."
    )
    material_name: str = Field(None, description="English name of the material.")

    phase: Optional[str] = Field(
        None, description="Phase description of material, such as anatase."
    )
    is_acronym: bool = Field(
        None, description="Whether the material is an acronym, such as LMO for LiMn2O4."
    )

    composition: List[Component] = Field(
        ..., description="List of components in this material."
    )
    amounts_vars: Dict[str, Values] = Field(
        {}, description="Amount variables (formula subscripts)."
    )
    elements_vars: Dict[str, List[str]] = Field(
        {}, description="Chemical element variables"
    )

    additives: List[str] = Field([], description="List of additives, dopants, etc.")
    oxygen_deficiency: Optional[str] = Field(
        None, description="Symbol indicating whether the materials is oxygen deficient."
    )
