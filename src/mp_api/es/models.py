from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from pymatgen.electronic_structure.core import Spin, OrbitalType
from pymatgen.core.periodic_table import Element
from datetime import datetime


class DataSource(Enum):
    """
    Type of electronic structure calculation
    """

    bandstructure = "bandstructure"
    dos = "dos"


class ProjectionType(Enum):
    """
    Type of projection data
    """

    total = "total"
    elements = "elements"
    orbitals = "orbitals"


class BSConvention(Enum):
    """
    The different conventions for k-path 
    selection in a band structure calculation
    """

    sc = "sc"
    hin = "hin"
    lm = "lm"


class DataType(Enum):
    """
    Type of electronic structure data
    """

    band_gap = "band_gap"
    cbm = "cbm"
    vbm = "vbm"


class ElectronicStructureDocument(BaseModel):
    task_id: str = Field(
        ..., title="Task ID", decription="The task ID for the material this electronic structure data corresponds to"
    )
    data_source: DataSource = Field(
        ..., title="Data Source", decription="Type of electronic structure calculation to use as data source"
    )
    projection_type: ProjectionType = Field(
        ProjectionType.total, title="Projection Type", decription="Type of projected data"
    )
    data_type: DataType = Field(..., title="Data Type", description="Type of electronic structure data")
    element: Optional[Element] = Field(
        None, title="Projection Element", description="Element to get projection data for"
    )
    orbital: Optional[OrbitalType] = Field(
        None, title="Projection Orbital", description="Orbital to get projection data for"
    )
    convention: Optional[BSConvention] = Field(
        BSConvention.sc, title="Band Structure Convention", description="k-path convention for the band structure"
    )
    spin: Spin = Field(Spin.up, title="Spin", description="Spin channel for the data")
    last_updated: datetime = Field(
        ...,
        title="Last Updated",
        description="timestamp for the most recent calculation for this electronic structure data",
    )
