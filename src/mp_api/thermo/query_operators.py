from typing import Optional
from collections import defaultdict
from fastapi import Query
from pymatgen.core import Element
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator


class ThermoChemicalQuery(QueryOperator):
    """
    Method to generate a query on chemical data associated with a thermo doc
    """

    def query(
        self,
        chemsys: Optional[str] = Query(
            None,
            description="Dash-delimited list of elements in the material.",
        ),
        elements: Optional[str] = Query(
            None,
            description="Elements in the material composition as a comma-separated list",
        ),
        nelements: Optional[int] = Query(
            None,
            description="Number of elements in the material",
        ),
    ):

        crit = {}  # type: dict

        if chemsys:
            eles = chemsys.split("-")
            chemsys = "-".join(sorted(eles))

            crit["chemsys"] = chemsys

        if elements:
            element_list = [Element(e) for e in elements.strip().split(",")]
            crit["elements"] = {"$all": [str(el) for el in element_list]}

        if nelements:
            crit["nelements"] = nelements

        return {"criteria": crit}


class IsStableQuery(QueryOperator):
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


class ThermoEnergyQuery(QueryOperator):
    """
    Method to generate a query for ranges of thermo energy data
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
            "thermo.energy": [energy_min, energy_max],
            "thermo.energy_per_atom": [energy_per_atom_min, energy_per_atom_max],
            "thermo.formation_energy_per_atom": [
                formation_energy_per_atom_min,
                formation_energy_per_atom_max,
            ],
            "thermo.e_above_hull": [e_above_hull_min, e_above_hull_max],
            "thermo.eq_reaction_e": [eq_reaction_min, eq_reaction_max],
            "thermo.explanation.corrected_energy": [
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
