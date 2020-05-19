from typing import List
from pydantic import BaseModel, Field
from pymatgen import Element
from datetime import datetime
from mp_api.materials.models import Structure, Composition, Status, CrystalSystem


class SymmetryData(BaseModel):
    """
    Defines a symmetry data set for materials documents
    """

    crystal_system: CrystalSystem = Field(
        None, title="Crystal System", description="The crystal system for this lattice"
    )

    symbol: str = Field(
        None,
        title="Space Group Symbol",
        description="The spacegroup symbol for the lattice",
    )

    number: int = Field(
        None,
        title="Space Group Number",
        description="The spacegroup number for the lattice",
    )

    point_group: str = Field(
        None, title="Point Group Symbol", description="The point group for the lattice"
    )

    symprec: float = Field(
        None,
        title="Symmetry Finding Precision",
        description="The precision given to spglib to determine the symmetry of this lattice",
    )

    version: str = Field(None, title="SPGLib version")


class MaterialsCoreDoc(BaseModel):
    """
    Definition for a core Materials Document
    Properties can inherit from MaterialProperty to define basic search metadata
    that links the property to this Material Document
    """

    structure: Structure = Field(
        None, description="The lowest energy structure for this material"
    )

    initial_structures: List[Structure] = Field(
        None,
        description="Initial structures used in the DFT optimizations corresponding to this material",
    )

    task_ids: List[str] = Field(
        None,
        title="Calculation IDs",
        description="List of Calculations IDS used to make this XAS spectrum",
    )

    state: Status = Field(
        None,
        description="Currrent state of this material document as either being referenced"
        "to an experimental structure, theoretical structure, or deprecated due to calcultion parameters",
    )

    task_id: str = Field(
        None,
        description="The ID of this material, used as a universal reference across proeprty documents."
        "This comes in the form: mp-******",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )
    created_at: datetime = Field(
        None,
        description="Timestamp for the first calculation for this Material document",
    )

    # Structure metadata
    nsites: int = Field(None, description="Total number of sites in the structure")
    elements: List[Element] = Field(
        None, description="List of elements in the material"
    )
    nelements: int = Field(None, title="Number of Elements")
    composition: Composition = Field(
        None, description="Full composition for the material"
    )
    composition_reduced: Composition = Field(
        None,
        title="Reduced Composition",
        description="Simplified representation of the composition",
    )
    formula_pretty: str = Field(
        None,
        title="Pretty Formula",
        description="Cleaned representation of the formula",
    )
    formula_anonymous: str = Field(
        None,
        title="Anonymous Formula",
        description="Anonymized representation of the formula",
    )
    chemsys: str = Field(
        None,
        title="Chemical System",
        description="dash-delimited string of elements in the material",
    )
    volume: float = Field(
        None,
        title="Volume",
        description="Total volume for this structure in Angstroms^3"
        # TODO Should be normalize to the formula unit?
    )

    density: float = Field(
        None, title="Density", description="Density in grams per cm^3"
    )

    density_atomic: float = Field(
        None,
        title="Packing Density",
        description="The atomic packing density in atoms per cm^3",
    )

    symmetry: SymmetryData = Field(None, description="Symmetry data for this material")

    deprecated: bool = Field(
        None, description="Whether the material is tagged as deprecated"
    )


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
        description=f"The ID for the material this property document corresponds to",
    )
