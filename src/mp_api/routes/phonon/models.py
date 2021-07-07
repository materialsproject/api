from typing import List
from datetime import datetime
from monty.json import MontyDecoder

from pydantic import BaseModel, Field, validator
from emmet.core.mpid import MPID
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import PhononDos


class PhononBSDOSDoc(BaseModel):
    """
    Phonon band structures and density of states data.
    """

    material_id: MPID = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    ph_bs: PhononBandStructureSymmLine = Field(
        None, description="Phonon band structure object",
    )

    ph_dos: PhononDos = Field(
        None, description="Phonon density of states object",
    )

    last_updated: datetime = Field(
        None,
        description="Timestamp for the most recent calculation for this Material document",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
