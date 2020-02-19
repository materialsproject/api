from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from pymatgen import Element

from mp_api.materials.models import Structure, Composition


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

    x: List[float] = Field(None, title="X-ray energy")
    y: List[float] = Field(None, title="Absorption (Arbitrary Units)")
    structure: Optional[Structure] = Field(None, title="Structure")
    absorbing_element: Optional[Element] = Field(None, title="Absoring Element")
    edge: Edge = Field(
        None, title="Absorption Edge", description="The interaction edge for XAS"
    )


class XASDoc(BaseModel):
    spectrum: XASSpectrum = None

    edge: Edge = Field(
        None, title="Absorption Edge", description="The interaction edge for XAS"
    )
    absorbing_element: Element = Field(None, title="Absoring Element")

    xas_ids: List[str] = Field(
        None,
        title="XAS IDs",
        description="List of FEFF Calculations IDS used to make this XAS spectrum",
    )
    task_id: str = Field(
        None,
        title="Task ID",
        description="The task ID for the material this spectrum corresponds to",
    )

    # Metadata from structure
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
    chemsys: Optional[str] = Field(
        None,
        title="Chemical System",
        description="dash-delimited string of elements in the material",
    )
    last_updated: datetime = Field(
        None,
        description="timestamp for the most recent calculation for this XAS spectrum",
    )
