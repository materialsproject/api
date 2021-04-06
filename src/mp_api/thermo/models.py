from typing import List, Dict, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from monty.json import MontyDecoder
from mp_api.materials.models import Composition
from mp_api.materials.models.doc import SymmetryData

from pymatgen.core import Element
from pymatgen.entries.computed_entries import ComputedEntry, ComputedStructureEntry


class DecompositionProduct(BaseModel):
    """
    Entry metadata for a decomposition process
    """

    material_id: str = Field(
        None, description="The material this decomposition points to"
    )
    formula: str = Field(
        None,
        description="The formula of the decomposed material this material decomposes to",
    )
    amount: float = Field(
        None,
        description="The amount of the decomposed material by formula units this this material decomposes to",
    )


class ThermoDoc(BaseModel):
    """
    A thermo entry document
    """

    material_id: str = Field(
        None,
        description="The ID of this material, used as a universal reference across property documents."
        "This comes in the form: mp-******",
    )

    property_name: str = Field(
        "thermo", description="The subfield name for this property"
    )

    uncorrected_energy_per_atom: float = Field(
        None, description="The total DFT energy of this material per atom in eV/atom"
    )

    energy_per_atom: float = Field(
        None,
        description="The total corrected DFT energy of this material per atom in eV/atom",
    )

    energy_uncertainy_per_atom: float = Field(None, description="")

    formation_energy_per_atom: float = Field(
        None, description="The formation energy per atom in eV/atom"
    )

    energy_above_hull: float = Field(
        None, description="The energy above the hull in eV/Atom"
    )

    is_stable: bool = Field(
        None,
        description="Flag for whether this material is on the hull and therefore stable",
    )

    equillibrium_reaction_energy_per_atom: float = Field(
        None,
        description="The reaction energy of a stable entry from the neighboring equilibrium stable materials in eV."
        " Also known as the inverse distance to hull.",
    )

    decomposes_to: List[DecompositionProduct] = Field(
        None,
        description="List of decomposition data for this material. Only valid for metastable or unstable material.",
    )

    energy_type: str = Field(
        None,
        description="The type of calculation this energy evaluation comes from. TODO: Convert to enum?",
    )

    entry_types: List[str] = Field(
        None, description="List of available energy types computed for this material"
    )

    entries: Dict[str, Union[ComputedEntry, ComputedStructureEntry]] = Field(
        None,
        description="List of all entries that are valid for this material."
        " The keys for this dictionary are names of various calculation types",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
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

    origins: List[dict] = Field(
        None, description="List of IDs used to populate data for the material"
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
