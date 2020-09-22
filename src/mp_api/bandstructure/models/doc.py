from typing import List, Union

from pydantic import BaseModel, Field, validator
from datetime import datetime
from monty.json import MontyDecoder
from pymatgen import Element

from mp_api.materials.models import Composition


class BSBandGap(BaseModel):
    """
    Band gap data model for band structures
    """

    direct: bool = Field(
        None, description="Whether the band gap is direct",
    )

    energy: float = Field(
        None, description="Energy of the band gap in eV",
    )

    transition: str = Field(
        None, description="K-points involved in transition across the gap",
    )


class BSBandMinMax(BaseModel):
    """
    Band minimum and maximum data model for band structures
    """

    band_index: dict = Field(
        None,
        description="Band energy indices of CBM or VBM points in band structure object",
    )

    kpoint_index: List[int] = Field(
        None,
        description="K-point indices of CBM or VBM points in band structure object",
    )

    kpoint: Union[str, List[str]] = Field(
        None, description="K-point(s) of CBM or VBM points",
    )

    energy: float = Field(
        None, description="Energy of CBM or VBM points in eV",
    )

    transition: Union[str, List[str]] = Field(
        None, description="K-points involved in transitions across the gap",
    )

    projection: dict = Field(
        None, description="Projection data for CBM or VBM points",
    )


class BSSummaryFields(BaseModel):
    """
    Band structure summary data fields for each convention
    """

    band_gap: BSBandGap = Field(
        None, description="Band gap data",
    )

    cbm: BSBandMinMax = Field(
        None, description="Conduction band minimum data",
    )

    vbm: BSBandMinMax = Field(
        None, description="Valence band maximum data",
    )

    nbands: Union[int, dict] = Field(
        None, description="Number of bands",
    )

    equivalent_labels: dict = Field(
        None, description="Equivalent k-point labels for the other path conventions",
    )

    task_id: str = Field(
        None, description="The Materials Project ID of the band structure calculation"
    )


class BSDoc(BaseModel):
    """
    Model for a document containing electronic structure summary data
    """

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    sc: BSSummaryFields = Field(
        None,
        description="Band structure summary data for the Setyawan-Curtarolo convention",
    )

    lm: BSSummaryFields = Field(
        None,
        description="Band structure summary data for the Latimer-Munro convention",
    )

    hin: BSSummaryFields = Field(
        None, description="Band structure summary data for the Hinuma convention",
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


class BSObjectReturn(BaseModel):
    mode: str = Field(None, description="Calculation mode of the band structure")

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the band structure calculation. This comes in the form: mp-******",
    )

    spin_polarized: bool = Field(
        None, description="Whether the band structure is spin polarized"
    )

    num_bands: int = Field(
        None, description="Number of bands included in the calculation"
    )

    efermi: float = Field(None, description="Fermi energy in eV")

    min_energy: float = Field(None, description="Minimum energy in eV")

    max_energy: float = Field(None, description="Maximum energy in eV")

    num_uniq_elements: int = Field(
        None, description="Number of unique elements in the material"
    )

    object: dict = Field(None, description="Band structure object data")

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)

