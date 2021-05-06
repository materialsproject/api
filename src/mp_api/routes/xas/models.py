from enum import Enum
from typing import List, Optional
from datetime import datetime

from monty.json import MontyDecoder
from pydantic import BaseModel, Field, validator

from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Structure

from mp_api.routes.materials.models.doc import MaterialProperty


class Edge(Enum):
    """
    The interaction edge for XAS
    There are 2n-1 sub-components to each edge where
    K: n=1
    L: n=2
    M: n=3
    N: n=4
    """

    K = "K"
    L2 = "L2"
    L3 = "L3"
    L2_3 = "L2,3"


class XASType(Enum):
    """
    Type of XAS Spectrum
    """

    XANES = "XANES"
    EXAFS = "EXAFS"
    XAFS = "XAFS"


class XASSpectrum(BaseModel):
    """
    Spectrum Data
    """

    x: List[float] = Field(None, title="X-ray energy")
    y: List[float] = Field(None, title="Absorption (Arbitrary Units)")
    structure: Optional[Structure] = Field(None, title="Structure")
    absorbing_element: Optional[Element] = Field(None, title="Absoring Element")
    edge: Edge = Field(
        None, title="Absorption Edge", description="The interaction edge for XAS"
    )


class XASDoc(MaterialProperty):
    """
    X-ray absorption spectra, absorption edge, absorbing element, ...
    """

    spectrum: Optional[XASSpectrum] = None

    edge: Edge = Field(
        None, title="Absorption Edge", description="The interaction edge for XAS"
    )
    absorbing_element: Element = Field(None, title="Absorbing Element")

    spectrum_type: XASType = Field(None, title="Type of XAS Spectrum")

    xas_id: str = Field(
        None, title="XAS Document ID", description="The unique ID for this XAS document"
    )

    task_id: str = Field(
        None, title="The material id for the material this document corresponds to"
    )

    xas_ids: List[str] = Field(
        None,
        title="Calculation IDs",
        description="List of Calculations IDS used to make this XAS spectrum",
    )

    last_updated: datetime = Field(
        None,
        description="timestamp for the most recent calculation for this XAS spectrum",
    )

    # Make sure that the datetime field is properly formatted
    @validator("last_updated", pre=True)
    def last_updated_dict_ok(cls, v):
        return MontyDecoder().process_decoded(v)
