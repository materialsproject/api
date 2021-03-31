from typing import List, Optional
from pymatgen.core.periodic_table import Element

from mp_api.materials.models import Structure, Composition
from mp_api.materials.models.doc import SymmetryData
from mp_api.xas.models import Edge, XASType
from mp_api.gb.models import GBTypeEnum

from pydantic import BaseModel, Field


class SearchStats(BaseModel):
    """
    Statistics about a specified SearchDoc field.
    """

    field: str = Field(
        None,
        title="Field",
        description="Field name corresponding to a field in SearchDoc",
    )
    num_samples: Optional[int] = Field(
        None,
        title="Sample",
        description="The number of documents sampled to generate statistics. "
        "If unspecified, statistics will be from entire database.",
    )
    min: float = Field(
        None,
        title="Minimum",
        description="The minimum value "
        "of the specified field used to "
        "generate statistics.",
    )
    max: float = Field(
        None,
        title="Maximum",
        description="The maximum value "
        "of the specified field used to "
        "generate statistics.",
    )
    median: float = Field(
        None, title="Median", description="The median of the field values."
    )
    mean: float = Field(None, title="Mean", description="The mean of the field values.")
    distribution: List[float] = Field(
        None,
        title="Distribution",
        description="List of floats specifying a kernel density "
        "estimator of the distribution, equally spaced "
        "between specified minimum and maximum values.",
    )


class XASSearchData(BaseModel):
    """
    Fields in XAS sub docs in search
    """

    edge: Edge = Field(
        None, title="Absorption Edge", description="The interaction edge for XAS"
    )
    absorbing_element: Element = Field(None, title="Absorbing Element")

    spectrum_type: XASType = Field(None, title="Type of XAS Spectrum")


class GBSearchData(BaseModel):
    """
    Fields in grain boundary sub docs in search
    """

    sigma: int = Field(
        None, description="Sigma value of the boundary",
    )

    type: GBTypeEnum = Field(
        None, description="Grain boundary type",
    )

    gb_energy: float = Field(
        None, description="Grain boundary energy in J/m^2",
    )

    rotation_angle: float = Field(
        None, description="Rotation angle in degrees",
    )


class SearchDoc(BaseModel):
    """
    Model for a document containing combined search data
    """

    # Materials

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

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

    symmetry: SymmetryData = Field(None, description="Symmetry data for this material")

    deprecated: bool = Field(
        None, description="Whether the material is tagged as deprecated"
    )

    structure: Structure = Field(
        None, description="The lowest energy structure for this material"
    )

    # Thermo

    energy: float = Field(
        None, description="Total DFT energy in eV.",
    )

    energy_per_atom: float = Field(
        None, description="Total DFT energy in eV/atom.",
    )

    formation_energy_per_atom: float = Field(
        None, description="Formation energy in eV/atom.",
    )

    e_above_hull: float = Field(
        None, description="Energy above the hull in eV/atom.",
    )

    eq_reaction_e: float = Field(
        None, description="Equilibrium reaction energy in eV/atom.",
    )

    corrected_energy: float = Field(
        None, description="Corrected DFT total energy in eV"
    )

    is_stable: bool = Field(
        None, description="Whether the material is stable.",
    )

    # XAS

    xas: List[XASSearchData] = Field(
        None, description="List of xas documents.",
    )

    # GB

    grain_boundaries: List[GBSearchData] = Field(
        None, description="List of grain boundary documents.",
    )

    # Band structure

    sc_energy: float = Field(
        None, description="Setyawan-Curtarolo band gap energy in eV.",
    )

    sc_direct: float = Field(
        None, description="Whether the Setyawan-Curtarolo band gap is direct.",
    )

    hin_energy: float = Field(
        None, description="Hinuma et al. band gap energy in eV.",
    )

    hin_direct: float = Field(
        None, description="Whether the Hinuma et al. band gap is direct.",
    )

    lm_energy: float = Field(
        None, description="Latimer-Munro band gap energy in eV.",
    )

    lm_direct: float = Field(
        None, description="Whether the Latimer-Munro band gap is direct.",
    )

    # DOS

    dos_energy_up: float = Field(
        None, description="Spin-up DOS band gap.",
    )

    dos_energy_down: float = Field(
        None, description="Spin-down DOS band gap.",
    )

    # Magnetism

    ordering: str = Field(
        None, description="Type of magnetic ordering.",
    )

    total_magnetization: float = Field(
        None, description="Total magnetization in μB.",
    )

    total_magnetization_normalized_vol: float = Field(
        None, description="Total magnetization normalized by volume in μB/Å³.",
    )

    total_magnetization_normalized_formula_units: float = Field(
        None, description="Total magnetization normalized by formula unit in μB/f.u. .",
    )

    # Elasticity

    k_voigt: float = Field(
        None, description="Voigt average of the bulk modulus.",
    )

    k_reuss: float = Field(
        None, description="Reuss average of the bulk modulus in GPa.",
    )

    k_vrh: float = Field(
        None, description="Voigt-Reuss-Hill average of the bulk modulus in GPa.",
    )

    g_voigt: float = Field(
        None, description="Voigt average of the shear modulus in GPa.",
    )

    g_reuss: float = Field(
        None, description="Reuss average of the shear modulus in GPa.",
    )

    g_vrh: float = Field(
        None, description="Voigt-Reuss-Hill average of the shear modulus in GPa.",
    )

    universal_anisotropy: float = Field(
        None, description="Elastic anisotropy.",
    )

    homogeneous_poisson: float = Field(
        None, description="Poisson's ratio.",
    )

    # Dielectric and Piezo

    e_total: float = Field(
        None, description="Total dielectric constant",
    )

    e_ionic: float = Field(
        None, description="Ionic contributio to dielectric constant",
    )

    e_static: float = Field(
        None, description="Electronic contribution to dielectric constant",
    )

    n: float = Field(
        None, description="Refractive index",
    )

    e_ij_max: float = Field(
        None, description="Piezoelectric modulus",
    )

    # Surface Properties

    weighted_surface_energy_EV_PER_ANG2: float = Field(
        None, description="Weighted surface energy in eV/Å²",
    )

    weighted_surface_energy: float = Field(
        None, description="Weighted surface energy in J/m²",
    )

    weighted_work_function: float = Field(
        None, description="Weighted work function in eV.",
    )

    surface_anisotropy: float = Field(
        None, description="Surface energy anisotropy.",
    )

    shape_factor: float = Field(
        None, description="Shape factor.",
    )

    # Has Props

    has_props: List[str] = Field(
        None, description="List of properties that are available for a given material.",
    )

    # Theoretical

    theoretical: bool = Field(
        None, description="Whether the material is theoretical.",
    )
