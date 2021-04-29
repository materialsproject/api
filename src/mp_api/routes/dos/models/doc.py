from typing import List

from pydantic import BaseModel, Field, validator
from datetime import datetime
from monty.json import MontyDecoder
from pymatgen.core.periodic_table import Element

from mp_api.routes.materials.models import Composition


class DOSSummaryFields(BaseModel):
    """
    Density of states summary data fields for each convention
    """

    band_gap: dict = Field(
        None, description="Band gap energies in eV for different spin channels",
    )

    cbm: dict = Field(
        None,
        description="Conduction band minimum energies in eV for different spin channels",
    )

    vbm: dict = Field(
        None,
        description="Valence band minimum energies in eV for different spin channels",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the density of states calculation. \
            This comes in the form: mp-******",
    )


class DOSOrbitals(BaseModel):
    """
    Model for density of states orbital projected data in an electronic structure doc
    """

    s: DOSSummaryFields = Field(
        None, description="S-orbital data",
    )

    p: DOSSummaryFields = Field(
        None, description="P-orbital data",
    )

    d: DOSSummaryFields = Field(
        None, description="D-orbital data",
    )


class DOSDoc(BaseModel):
    """
    Model for a document containing electronic structure summary data
    """

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    total: DOSSummaryFields = Field(
        None, description="Total density of states summary data",
    )

    elemental: dict = Field(
        None, description="Element projected density of states summary data",
    )

    orbital: dict = Field(
        None, description="Orbital projected density of states summary data",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the density of states calculation",
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
        description="Total volume for this structure in Angstroms^3",
    )

    density: float = Field(
        None, title="Density", description="Density in grams per cm^3"
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)


class DOSObjectReturn(BaseModel):

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the density of states calculation. This comes in the form: mp-******",
    )

    efermi: float = Field(None, description="Fermi energy in eV")

    min_energy: float = Field(None, description="Minimum energy in eV")

    max_energy: float = Field(None, description="Maximum energy in eV")

    num_uniq_elements: int = Field(
        None, description="Number of unique elements in the material"
    )

    object: dict = Field(None, description="Density of states object data")

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
