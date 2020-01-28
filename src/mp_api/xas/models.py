from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from pymatgen import Element

from mp_api.core.models import Structure, Composition


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
    TOTAL = "Total"


class XASSpectrum(BaseModel):
    """
    Spectrum Data
    """

    x: List[float] = Field(..., title="X-ray energy")
    y: List[float] = Field(..., title="Absorption (Arbitrary Units)")
    structure: Optional[Structure] = Field(None, title="Structure")
    absorbing_element: Optional[Element] = Field(..., title="Absoring Element")
    edge: Edge = Field(
        ..., title="Absorption Edge", description="The interaction edge for XAS"
    )


class XASDoc(BaseModel):
    spectrum: XASSpectrum

    edge: Edge = Field(
        ..., title="Absorption Edge", description="The interaction edge for XAS"
    )
    absorbing_element: Element = Field(..., title="Absoring Element")

    xas_ids: List[str] = Field(
        ...,
        title="XAS IDs",
        description="List of FEFF Calculations IDS used to make this XAS spectrum",
    )
    task_id: str = Field(
        ...,
        title="Task ID",
        description="The task ID for the material this spectrum corresponds to",
    )

    # Metadata from structure
    elements: List[Element] = Field(..., description="List of elements in the material")
    nelements: int = Field(..., title="Number of Elements")
    composition: Composition = Field(
        ..., description="Full composition for the material"
    )
    composition_reduced: Composition = Field(
        ...,
        title="Reduced Composition",
        description="Simplified representation of the composition",
    )
    formula_pretty: str = Field(
        ..., title="Pretty Formula", description="Cleaned representation of the formula"
    )
    formula_anonymous: str = Field(
        ...,
        title="Anonymous Formula",
        description="Anonymized representation of the formula",
    )
    chemsys: str = Field(
        ...,
        title="Chemical System",
        description="dash-delimited string of elements in the material",
    )
    last_updated: datetime = Field(
        ...,
        description="timestamp for the most recent calculation for this XAS spectrum",
    )


class XASSearchResponse(BaseModel):
    """
    Unique index for XAS spectra by searching
    """ 
    task_id: str = Field(
        ...,
        title="Task ID",
        description="The task ID for the material this spectrum corresponds to",
    )
    edge: Edge = Field(
        ..., title="Absorption Edge", description="The interaction edge for XAS"
    )
    absorbing_element: Element = Field(..., title="Absoring Element")
