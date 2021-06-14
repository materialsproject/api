from typing import List
from datetime import datetime
from monty.json import MontyDecoder

from pydantic import BaseModel, Field, validator
from pymatgen.core import Structure
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine


class PhononBS(BaseModel):
    """
    Model for a phonon band structure object
    """

    eigendisplacements: dict = Field(
        None, description="Phonon eigendisplacements in cartesian coordinates",
    )

    has_nac: bool = Field(
        None, description="Whether non-analytical corrections at Gamma are included",
    )

    bands: List[List[float]] = Field(
        None, description="Phonon band eigenvalues in eV",
    )

    qpoints: List[List[float]] = Field(
        None,
        description="List of q-points in fractional coordinates of the reciprocal lattice",
    )

    labels_dict: dict = Field(
        None, description="q-point labels dictionary",
    )

    lattice_rec: dict = Field(
        None, description="Reciprocal lattice of the structure",
    )

    structure: Structure = Field(
        None, description="Structure of the material",
    )

    class Config:
        extra = "allow"


class PhononBSDoc(BaseModel):
    """
    Phonon band structures.
    """

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    ph_bs: PhononBandStructureSymmLine = Field(
        None, description="Phonon band structure object",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)


class PhononImgDoc(BaseModel):
    """
    Model for a document containing phonon image data.
    """

    plot: bytes = Field(
        None, description="Plot image data.",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    last_updated: datetime = Field(
        None, description="Timestamp for the most recent calculation for this document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)

    # Make sure that the plot field is properly formatted
    @validator("plot", pre=True)
    def plot_bytes_ok(cls, v):
        return str(v)
