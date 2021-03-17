from enum import Enum
from typing import Optional
from fastapi import Query

from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.magnetism.models import MagneticOrderingEnum

from collections import defaultdict


class HasPropsEnum(Enum):
    magnetism = "magnetism"
    piezoelectric = "piezoelectric"
    dielectric = "dielectric"
    elasticity = "elasticity"
    surface_properties = "surface_properties"
    bandstructure = "bandstructure"
    dos = "dos"
    xas = "xas"
    grain_boundaries = "grain_boundaries"
    eos = "eos"


class HasPropsQuery(QueryOperator):
    """
    Method to generate a query on whether a material has a certain property
    """

    def query(
        self,
        has_props: Optional[str] = Query(
            None,
            description="Comma-delimited list of possible properties given by HasPropsEnum to search for.",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if has_props:
            crit = {"has_props": {"$all": has_props.split(",")}}

        return {"criteria": crit}


class SearchBandGapQuery(QueryOperator):
    """
    Method to generate a query for ranges of band gap data in search docs
    """

    def query(
        self,
        sc_band_gap_max: Optional[float] = Query(
            None,
            description="Maximum value for the Setyawan-Curtarolo band gap in eV.",
        ),
        sc_band_gap_min: Optional[float] = Query(
            None,
            description="Minimum value for the Setyawan-Curtarolo band gap in eV.",
        ),
        sc_direct: Optional[bool] = Query(
            None, description="Whether the Setyawan-Curtarolo band gap is direct.",
        ),
        hin_band_gap_max: Optional[float] = Query(
            None, description="Maximum value for the Hinuma et al. band gap in eV.",
        ),
        hin_band_gap_min: Optional[float] = Query(
            None, description="Minimum value for the Hinuma et al. band gap in eV.",
        ),
        hin_direct: Optional[bool] = Query(
            None, description="Whether the Hinuma et al. band gap is direct.",
        ),
        lm_band_gap_max: Optional[float] = Query(
            None, description="Maximum value for the Latimer-Munro band gap in eV.",
        ),
        lm_band_gap_min: Optional[float] = Query(
            None, description="Minimum value for the Latimer-Munro band gap in eV.",
        ),
        lm_direct: Optional[bool] = Query(
            None, description="Whether the Latimer-Munro band gap is direct.",
        ),
        dos_band_gap_up_max: Optional[float] = Query(
            None, description="Maximum value for the DOS spin-up band gap in eV.",
        ),
        dos_band_gap_up_min: Optional[float] = Query(
            None, description="Minimum value for the DOS spin-up band gap in eV.",
        ),
        dos_band_gap_down_max: Optional[float] = Query(
            None, description="Maximum value for the DOS spin-down band gap in eV.",
        ),
        dos_band_gap_down_min: Optional[float] = Query(
            None, description="Minimum value for the DOS spin-down band gap in eV.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "sc_energy": [sc_band_gap_min, sc_band_gap_max],
            "hin_energy": [hin_band_gap_min, hin_band_gap_max],
            "lm_energy": [lm_band_gap_min, lm_band_gap_max],
            "dos_energy_up": [dos_band_gap_up_min, dos_band_gap_up_max],
            "dos_energy_down": [dos_band_gap_down_min, dos_band_gap_down_max],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        if sc_direct is not None:
            crit["sc_direct"] = sc_direct

        if hin_direct is not None:
            crit["hin_direct"] = hin_direct

        if lm_direct is not None:
            crit["lm_direct"] = lm_direct

        return {"criteria": crit}


class ThermoEnergySearchQuery(QueryOperator):
    """
    Method to generate a query for ranges of thermo energy data in search docs
    """

    def query(
        self,
        energy_max: Optional[float] = Query(
            None, description="Maximum value for the total energy in eV.",
        ),
        energy_min: Optional[float] = Query(
            None, description="Minimum value for the total energy in eV.",
        ),
        energy_per_atom_max: Optional[float] = Query(
            None, description="Maximum value for the total energy in eV/atom.",
        ),
        energy_per_atom_min: Optional[float] = Query(
            None, description="Minimum value for the total energy in eV/atom.",
        ),
        formation_energy_per_atom_max: Optional[float] = Query(
            None, description="Maximum value for the formation energy in eV/atom.",
        ),
        formation_energy_per_atom_min: Optional[float] = Query(
            None, description="Minimum value for the formation energy in eV/atom.",
        ),
        e_above_hull_max: Optional[float] = Query(
            None, description="Maximum value for the energy above the hull in eV/atom.",
        ),
        e_above_hull_min: Optional[float] = Query(
            None, description="Minimum value for the energy above the hull in eV/atom.",
        ),
        eq_reaction_max: Optional[float] = Query(
            None,
            description="Maximum value for the equilibrium reaction energy in eV/atom.",
        ),
        eq_reaction_min: Optional[float] = Query(
            None,
            description="Minimum value for the equilibrium reaction energy in eV/atom.",
        ),
        corrected_energy_max: Optional[float] = Query(
            None, description="Maximum value for the corrected total energy in eV.",
        ),
        corrected_energy_min: Optional[float] = Query(
            None, description="Minimum value for the corrected total energy in eV.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "energy": [energy_min, energy_max],
            "energy_per_atom": [energy_per_atom_min, energy_per_atom_max],
            "formation_energy_per_atom": [
                formation_energy_per_atom_min,
                formation_energy_per_atom_max,
            ],
            "e_above_hull": [e_above_hull_min, e_above_hull_max],
            "eq_reaction_e": [eq_reaction_min, eq_reaction_max],
            "explanation.corrected_energy": [
                corrected_energy_min,
                corrected_energy_max,
            ],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class SearchIsStableQuery(QueryOperator):
    """
    Method to generate a query on whether a material is stable
    """

    def query(
        self,
        is_stable: Optional[bool] = Query(
            None, description="Whether the material is stable."
        ),
    ):

        crit = {}

        if is_stable is not None:
            crit["is_stable"] = is_stable

        return {"criteria": crit}


class SearchElasticityQuery(QueryOperator):
    """
    Method to generate a query for ranges of elasticity data in search docs
    """

    def query(
        self,
        k_voigt_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt average of the bulk modulus in GPa.",
        ),
        k_voigt_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt average of the bulk modulus in GPa.",
        ),
        k_reuss_max: Optional[float] = Query(
            None,
            description="Maximum value for the Reuss average of the bulk modulus in GPa.",
        ),
        k_reuss_min: Optional[float] = Query(
            None,
            description="Minimum value for the Reuss average of the bulk modulus in GPa.",
        ),
        k_vrh_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt-Reuss-Hill average of the bulk modulus in GPa.",
        ),
        k_vrh_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt-Reuss-Hill average of the bulk modulus in GPa.",
        ),
        g_voigt_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt average of the shear modulus in GPa.",
        ),
        g_voigt_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt average of the shear modulus in GPa.",
        ),
        g_reuss_max: Optional[float] = Query(
            None,
            description="Maximum value for the Reuss average of the shear modulus in GPa.",
        ),
        g_reuss_min: Optional[float] = Query(
            None,
            description="Minimum value for the Reuss average of the shear modulus in GPa.",
        ),
        g_vrh_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt-Reuss-Hill average of the shear modulus in GPa.",
        ),
        g_vrh_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt-Reuss-Hill average of the shear modulus in GPa.",
        ),
        elastic_anisotropy_max: Optional[float] = Query(
            None, description="Maximum value for the elastic anisotropy.",
        ),
        elastic_anisotropy_min: Optional[float] = Query(
            None, description="Maximum value for the elastic anisotropy.",
        ),
        poisson_max: Optional[float] = Query(
            None, description="Maximum value for Poisson's ratio.",
        ),
        poisson_min: Optional[float] = Query(
            None, description="Minimum value for Poisson's ratio.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "k_voigt": [k_voigt_min, k_voigt_max],
            "k_reuss": [k_reuss_min, k_reuss_max],
            "k_vrh": [k_vrh_min, k_vrh_max],
            "g_voigt": [g_voigt_min, g_voigt_max],
            "g_reuss": [g_reuss_min, g_reuss_max],
            "g_vrh": [g_vrh_min, g_vrh_max],
            "universal_anisotropy": [elastic_anisotropy_min, elastic_anisotropy_max],
            "homogeneous_poisson": [poisson_min, poisson_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class SearchMagneticQuery(QueryOperator):
    """
    Method to generate a query for magnetic data in search docs.
    """

    def query(
        self,
        ordering: Optional[MagneticOrderingEnum] = Query(
            None, description="Magnetic ordering of the material."
        ),
        total_magnetization_max: Optional[float] = Query(
            None, description="Maximum value for the total magnetization.",
        ),
        total_magnetization_min: Optional[float] = Query(
            None, description="Minimum value for the total magnetization.",
        ),
        total_magnetization_normalized_vol_max: Optional[float] = Query(
            None,
            description="Maximum value for the total magnetization normalized with volume.",
        ),
        total_magnetization_normalized_vol_min: Optional[float] = Query(
            None,
            description="Minimum value for the total magnetization normalized with volume.",
        ),
        total_magnetization_normalized_formula_units_max: Optional[float] = Query(
            None,
            description="Maximum value for the total magnetization normalized with formula units.",
        ),
        total_magnetization_normalized_formula_units_min: Optional[float] = Query(
            None,
            description="Minimum value for the total magnetization normalized with formula units.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "total_magnetization": [total_magnetization_min, total_magnetization_max],
            "total_magnetization_normalized_vol": [
                total_magnetization_normalized_vol_min,
                total_magnetization_normalized_vol_max,
            ],
            "total_magnetization_normalized_formula_units": [
                total_magnetization_normalized_formula_units_min,
                total_magnetization_normalized_formula_units_max,
            ],
        }  # type: dict

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        if ordering:
            crit["ordering"] = ordering.value

        return {"criteria": crit}


class SearchDielectricPiezoQuery(QueryOperator):
    """
    Method to generate a query for ranges of dielectric and piezo data in search docs
    """

    def query(
        self,
        e_total_max: Optional[float] = Query(
            None, description="Maximum value for the total dielectric constant.",
        ),
        e_total_min: Optional[float] = Query(
            None, description="Minimum value for the total dielectric constant.",
        ),
        e_ionic_max: Optional[float] = Query(
            None, description="Maximum value for the ionic dielectric constant.",
        ),
        e_ionic_min: Optional[float] = Query(
            None, description="Minimum value for the ionic dielectric constant.",
        ),
        e_static_max: Optional[float] = Query(
            None, description="Maximum value for the static dielectric constant.",
        ),
        e_static_min: Optional[float] = Query(
            None, description="Minimum value for the static dielectric constant.",
        ),
        n_max: Optional[float] = Query(
            None, description="Maximum value for the refractive index.",
        ),
        n_min: Optional[float] = Query(
            None, description="Minimum value for the refractive index.",
        ),
        piezo_modulus_max: Optional[float] = Query(
            None, description="Maximum value for the piezoelectric modulus in C/m².",
        ),
        piezo_modulus_min: Optional[float] = Query(
            None, description="Minimum value for the piezoelectric modulus in C/m².",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "e_total": [e_total_min, e_total_max],
            "e_ionic": [e_ionic_min, e_ionic_max],
            "e_static": [e_static_min, e_static_max],
            "n": [n_min, n_max],
            "e_ij_max": [piezo_modulus_min, piezo_modulus_max],
        }

        for entry in d:
            if d[entry][0]:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1]:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


# TODO:
# XAS and GB sub doc query operators
# Add weighted work function to data
# Add dimensionality to search endpoint
# Add "has_reconstructed" data
