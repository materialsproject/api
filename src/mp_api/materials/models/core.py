from typing import Dict, List, Optional, Union, Tuple
from pydantic import BaseModel, Field, ConstrainedInt
from typing_extensions import Literal
from pymatgen import Element
from enum import Enum
from pymatgen.symmetry.groups import SYMM_DATA

Vector3D = Tuple[float, float, float]


class Lattice(BaseModel):
    """
    A lattice object represented as a 3x3 matrix of floats in Angstroms
    """

    a: float = Field(..., title="*a* lattice parameter")
    alpha: int = Field(..., title="Angle between a and b lattice vectors")
    b: float = Field(..., title="b lattice parameter")
    beta: int = Field(..., title="Angle between a and c lattice vectors")
    c: float = Field(..., title="c lattice parameter")
    gamma: int = Field(..., title="Angle between b and c lattice vectors")
    volume: float = Field(..., title="Lattice volume")

    matrix: Tuple[Vector3D, Vector3D, Vector3D] = Field(
        ..., description="Matrix representation of this lattice"
    )


class Specie(BaseModel):
    """
    An extension of Element with an oxidation state and other optional
    properties. Properties associated with Specie should be "idealized"
    values, not calculated values. For example, high-spin Fe2+ may be
    assigned an idealized spin of +5, but an actual Fe2+ site may be
    calculated to have a magmom of +4.5. Calculated properties should be
    assigned to Site objects, and not Specie.
    """

    symbol: str = Field(..., title="Element Symbol")
    oxidation_state: float = Field(..., title="Oxidation State")
    properties: Optional[Dict] = Field(..., title="Species Properties")


Composition = Dict[Element, float]
Composition.__doc__ = """A dictionary mapping element to total quantity"""


class SiteSpecie(Specie):
    """
    Adds site occupation to Species
    """

    occu: float = Field(..., title="Occupation")


class SiteElement(BaseModel):
    """
    Elements defined on site with an occupation
    """

    element: Element = Field(..., title="Element")
    occu: float = Field(..., title="Occupation")


class Site(BaseModel):
    """
    A generalized *non-periodic* site. This is essentially a composition
    at a point in space, with some optional properties associated with it. A
    Composition is used to represent the atoms and occupancy, which allows for
    disordered site representation. Coords are given in standard cartesian
    coordinates.
    """

    species: List[Union[SiteElement, SiteSpecie]] = Field(..., title="Species")
    xyz: Tuple[float, float, float] = Field(..., title="Cartesian Coordinates")
    label: str = Field(..., title="Label")
    properties: Optional[Dict] = Field(None, title="Properties")


class PeriodicSite(Site):
    """
    A generalized *periodic* site. This adds on fractional coordinates within the
    lattice to the generalized Site model
    """

    abc: Tuple[float, float, float] = Field(..., title="Fractional Coordinates")


class Structure(BaseModel):
    """
    Basic Structure object with periodicity. Essentially a sequence
    of Sites having a common lattice and a total charge.
    """

    charge: Optional[float] = Field(None, title="Total charge")
    lattice: Lattice = Field(..., title="Lattice for this structure")
    sites: List[PeriodicSite] = Field(..., title="List of sites in this structure")


class Status(Enum):
    """
    """

    exp = "Experimental"
    theo = "Theoretical"
    deprecated = "Deprecated"


SpacegroupSymbol = Literal[SYMM_DATA["space_group_encoding"].keys()]
SpacegroupSymbol.__doc__ = """The Hoenfield-Schfonberg space group symbol"""

SpacegroupNumber = ConstrainedInt(gt=0, le=265)
SpacegroupNumber.__doc__ = (
    """The space group number as defined by Hoenfield-Schfonber"""
)

PointGroupSymbol = Literal[SYMM_DATA["point_group_encoding"].keys()]
PointGroupSymbol.__doc__ = """The point group symbol"""


class CrystalSystem(Enum):
    """
    The crystal system of the lattice
    """

    tri = "Triclinic"
    mono = "Monoclinic"
    ortho = "Orthorhombic"
    tet = "Tetragonal"
    trig = "Triganol"
    hex = "Hexagonal"
    cubic = "Cubic"
