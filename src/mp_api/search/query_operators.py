from enum import Enum
from typing import Optional
from fastapi import Query

from mp_api.core.query_operator import STORE_PARAMS, QueryOperator


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
            None,
            description="Whether the Setyawan-Curtarolo band gap is direct.",
        ),
        hin_band_gap_max: Optional[float] = Query(
            None,
            description="Maximum value for the Hinuma et al. band gap in eV.",
        ),
        hin_band_gap_min: Optional[float] = Query(
            None,
            description="Minimum value for the Hinuma et al. band gap in eV.",
        ),
        hin_direct: Optional[bool] = Query(
            None,
            description="Whether the Hinuma et al. band gap is direct.",
        ),
        lm_band_gap_max: Optional[float] = Query(
            None,
            description="Maximum value for the Latimer-Munro band gap in eV.",
        ),
        lm_band_gap_min: Optional[float] = Query(
            None,
            description="Minimum value for the Latimer-Munro band gap in eV.",
        ),
        lm_direct: Optional[bool] = Query(
            None,
            description="Whether the Latimer-Munro band gap is direct.",
        ),
        dos_band_gap_up_max: Optional[float] = Query(
            None,
            description="Maximum value for the DOS spin-up band gap in eV.",
        ),
        dos_band_gap_up_min: Optional[float] = Query(
            None,
            description="Minimum value for the DOS spin-up band gap in eV.",
        ),
        dos_band_gap_down_max: Optional[float] = Query(
            None,
            description="Maximum value for the DOS spin-down band gap in eV.",
        ),
        dos_band_gap_down_min: Optional[float] = Query(
            None,
            description="Minimum value for the DOS spin-down band gap in eV.",
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
            None,
            description="Maximum value for the total energy in eV.",
        ),
        energy_min: Optional[float] = Query(
            None,
            description="Minimum value for the total energy in eV.",
        ),
        energy_per_atom_max: Optional[float] = Query(
            None,
            description="Maximum value for the total energy in eV/atom.",
        ),
        energy_per_atom_min: Optional[float] = Query(
            None,
            description="Minimum value for the total energy in eV/atom.",
        ),
        formation_energy_per_atom_max: Optional[float] = Query(
            None,
            description="Maximum value for the formation energy in eV/atom.",
        ),
        formation_energy_per_atom_min: Optional[float] = Query(
            None,
            description="Minimum value for the formation energy in eV/atom.",
        ),
        e_above_hull_max: Optional[float] = Query(
            None,
            description="Maximum value for the energy above the hull in eV/atom.",
        ),
        e_above_hull_min: Optional[float] = Query(
            None,
            description="Minimum value for the energy above the hull in eV/atom.",
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
            None,
            description="Maximum value for the corrected total energy in eV.",
        ),
        corrected_energy_min: Optional[float] = Query(
            None,
            description="Minimum value for the corrected total energy in eV.",
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


class SearchTaskIDsQuery(QueryOperator):
    """
    Method to generate a query on search docs using multiple task_id values
    """

    def query(
        self,
        task_ids: Optional[str] = Query(
            None, description="Comma-separated list of task_ids to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if task_ids:
            crit.update({"task_id": {"$in": task_ids.split(",")}})

        return {"criteria": crit}


# TODO:
# XAS and GB sub doc query operators
# Magnetism query ops from endpoint
