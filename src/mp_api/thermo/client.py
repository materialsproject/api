from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester, MPRestError
from mp_api.thermo.models import ThermoDoc

import warnings


class ThermoRester(BaseRester):

    suffix = "thermo"
    document_model = ThermoDoc

    def search_thermo_docs(
        self,
        chemsys: Optional[str] = None,
        nelements: Optional[int] = None,
        total_energy: Optional[Tuple[float, float]] = None,
        total_energy_per_atom: Optional[Tuple[float, float]] = None,
        corrected_total_energy: Optional[Tuple[float, float]] = None,
        formation_energy: Optional[Tuple[float, float]] = None,
        energy_above_hull: Optional[Tuple[float, float]] = None,
        eq_reaction_energy: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            chemsys (str): Dash-delimited string of elements in the material.
            nelements (int): Number of elements in the material.
            total_energy (Tuple[float,float]): Minimum and maximum total DFT energy in eV to consider.
            total_energy_per_atom (Tuple[float,float]): Minimum and maximum total DFT energy in eV/atom to consider.
            corrected_total_energy (Tuple[float,float]): Minimum and maximum corrected total DFT energy
                in eV to consider.
            formation_energy (Tuple[float,float]): Minimum and maximum formation energy in eV/atom to consider.
            energy_above_hull (Tuple[float,float]): Minimum and maximum energy above the hull in eV/atom to consider.
            eq_reaction_energy (Tuple[float,float]): Minimum and maximum equilibrium reaction energy in eV/atom to
                consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs only.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

        if chemsys:
            query_params.update({"chemsys": chemsys})

        if nelements:
            query_params.update({"nelements": nelements})

        if total_energy:
            query_params.update(
                {"energy_min": total_energy[0], "energy_max": total_energy[1]}
            )

        if total_energy_per_atom:
            query_params.update(
                {
                    "energy_per_atom_min": total_energy_per_atom[0],
                    "energy_per_atom_max": total_energy_per_atom[1],
                }
            )

        if corrected_total_energy:
            query_params.update(
                {
                    "corrected_energy_min": corrected_total_energy[0],
                    "corrected_energy_max": corrected_total_energy[1],
                }
            )

        if formation_energy:
            query_params.update(
                {
                    "formation_energy_per_atom_min": formation_energy[0],
                    "formation_energy_per_atom_max": formation_energy[1],
                }
            )

        if eq_reaction_energy:
            query_params.update(
                {
                    "eq_reaction_min": eq_reaction_energy[0],
                    "eq_reaction_max": eq_reaction_energy[1],
                }
            )

        if energy_above_hull:
            query_params.update(
                {
                    "e_above_hull_min": energy_above_hull[0],
                    "e_above_hull_max": energy_above_hull[1],
                }
            )

        if fields:
            query_params.update({"fields": ",".join(fields)})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results
