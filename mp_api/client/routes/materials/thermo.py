from __future__ import annotations

import logging
from collections import defaultdict
from copy import deepcopy
from typing import TYPE_CHECKING

import numpy as np
from emmet.core.thermo import ThermoDoc, validate_thermo_id
from emmet.core.types.enums import ThermoType
from emmet.core.types.pymatgen_types.phase_diagram_adapter import PhaseDiagramType
from pydantic import TypeAdapter
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Element
from pymatgen.entries.computed_entries import ConstantEnergyAdjustment

from mp_api.client.core import BaseRester
from mp_api.client.core._display import status
from mp_api.client.core.client import LATEST_DB_VERSION, _normalize_db_version
from mp_api.client.core.exceptions import MPRestError
from mp_api.client.core.settings import DEFAULT_THERMOTYPE
from mp_api.client.core.utils import to_partition_version, validate_ids

if TYPE_CHECKING:
    from collections.abc import Sequence

    from enums import Enum

logger = logging.getLogger(__name__)


def _accessible_entries(entries: list, elements: list) -> list:
    """The entries of a pre-built GGA(+U)/r2SCAN phase diagram without the access-
    controlled (BY-NC licensed, GNoMe) ones, with energies as if mixed without them.

    The GNoMe entries are r2SCAN-only, so they do not affect the mixing state or the
    other entries' energies, except in r2SCAN-anchored systems: there the mixing scheme
    places GGA(+U)-only entries onto the r2SCAN hull (shifting them by the r2SCAN minus
    the GGA(+U) hull energy at their composition), which includes the GNoMe entries.
    These are re-referenced to the r2SCAN hull without them, as a re-mix would give.
    """
    accessible = [e for e in entries if e.data.get("license") != "BY-NC"]
    shifted = [
        i
        for i, e in enumerate(accessible)
        if any(
            "onto the r2SCAN hull" in (a.description or "")
            for a in e.energy_adjustments
        )
    ]
    if not shifted:
        return accessible

    r2scan = [
        e for e in entries if str(e.parameters.get("run_type")).lower() == "r2scan"
    ]
    full_hull = PhaseDiagram(r2scan, elements=elements)
    accessible_hull = PhaseDiagram(
        [e for e in r2scan if e.data.get("license") != "BY-NC"], elements=elements
    )
    for i in shifted:
        comp = accessible[i].composition
        shift = accessible_hull.get_hull_energy_per_atom(comp)
        shift -= full_hull.get_hull_energy_per_atom(comp)
        if shift > 1e-10:  # (beyond float noise) copy, to leave the served entry as is:
            entry = accessible[i] = deepcopy(accessible[i])
            entry.energy_adjustments.append(
                ConstantEnergyAdjustment(
                    shift * comp.num_atoms,
                    name="MP GGA(+U)/r2SCAN mixing adjustment, without GNoMe entries",
                    description="Place GGA(+U) energy onto the r2SCAN hull without the "
                    "access-controlled (GNoMe) entries",
                )
            )
    return accessible


class ThermoRester(BaseRester):
    suffix = "materials/thermo"
    document_model = ThermoDoc  # type: ignore
    primary_key = "material_id"

    @staticmethod
    def _check_thermo_types(thermo_types: Sequence[str | Enum]) -> set[str]:
        """Check if a user has input any invalid thermo types.

        Args:
        thermo_types (Sequence of str or Enum) : list of thermo types
            the user has queried for

        phase-diagram tbl has "r2SCAN", not "R2SCAN"
        mixing of ThermoType/RunType in emmet -_-
        TODO: coerce upstream? allow case-insensitivity in emmet?

        Returns:
        set of str: validated thermo types

        Raises:
        ValueError if any invalid thermo types are input
        """
        t_types: set[str] = {t if isinstance(t, str) else t.value for t in thermo_types}
        t_types = {"r2SCAN" if t == "R2SCAN" else t for t in t_types}
        valid_types = {"r2SCAN", *map(str, ThermoType.__members__.values())}

        if invalid_types := t_types - valid_types:
            raise ValueError(
                f"Invalid thermo type(s) passed: {invalid_types}, valid types are: {valid_types}"
            )
        return t_types

    def search(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | list[str] | None = None,
        energy_above_hull: tuple[float, float] | None = None,
        equilibrium_reaction_energy: tuple[float, float] | None = None,
        formation_energy: tuple[float, float] | None = None,
        formula: str | list[str] | None = None,
        is_stable: bool | None = None,
        num_elements: tuple[int, int] | None = None,
        thermo_ids: list[str] | None = None,
        thermo_types: list[ThermoType | str] | None = None,
        total_energy: tuple[float, float] | None = None,
        uncorrected_energy: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
        db_version: str | None = None,
    ) -> list[ThermoDoc] | list[dict]:
        """Query core thermo docs using a variety of search criteria.

        Arguments:
            material_ids (str | list[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            chemsys (str | list[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            energy_above_hull (tuple[float, float]): Minimum and maximum energy above the hull in eV/atom to consider.
            equilibrium_reaction_energy (tuple[float, float]): Minimum and maximum equilibrium reaction energy
                in eV/atom to consider.
            formation_energy (tuple[float, float]): Minimum and maximum formation energy in eV/atom to consider.
            formula (str | list[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            is_stable (bool): Whether the material is stable.
            material_ids (list[str]): List of Materials Project IDs to return data for.
            thermo_ids (list[str]): List of thermo IDs to return data for. This is a combination of the Materials
                Project ID and thermo type (e.g. mp-149_GGA_GGA+U).
            thermo_types (list[ThermoType | str]): List of thermo/run types to return data for (e.g. ThermoType.GGA_GGA_U).
            num_elements (tuple[int, int]): Minimum and maximum number of elements in the material to consider.
            total_energy (tuple[float, float]): Minimum and maximum corrected total energy in eV/atom to consider.
            uncorrected_energy (tuple[float, float]): Minimum and maximum uncorrected total
                energy in eV/atom to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (list[str]): List of fields in ThermoDoc to return data for.
                Default is material_id and last_updated if all_fields is False.
            db_version (str | None): Database version to download when no filters are given
                (full dataset), e.g. "2026.04.13" or "latest". Defaults to the rester's version.
                See `available_db_versions()`.

        Returns:
            ([ThermoDoc], [dict]) List of thermo documents or dictionaries.
        """
        query_params: dict = defaultdict(dict)

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if thermo_ids:
            try:
                for thermo_id in thermo_ids:
                    validate_thermo_id(thermo_id)
                query_params.update({"thermo_ids": ",".join(thermo_ids)})

            except Exception:
                raise MPRestError(
                    f"At least one thermo_id in: {thermo_ids} is invalid."
                    " Try using the validate_thermo_id function from emmet.core.thermo"
                    " to test your inputs."
                )

        if thermo_types:
            query_params.update(
                {"thermo_types": ",".join(self._check_thermo_types(thermo_types))}
            )

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if is_stable is not None:
            query_params.update({"is_stable": is_stable})

        name_dict = {
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "energy_above_hull": "energy_above_hull",
            "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
            "uncorrected_energy": "uncorrected_energy_per_atom",
        }

        for param, value in locals().items():
            if "energy" in param and value:
                query_params.update(
                    {
                        f"{name_dict[param]}_min": value[0],
                        f"{name_dict[param]}_max": value[1],
                    }
                )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(  # type: ignore[return-value]
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
            db_version=db_version,
        )

    def get_phase_diagram_from_chemsys(
        self,
        chemsys: str,
        thermo_type: ThermoType | str = DEFAULT_THERMOTYPE,
        db_version: str | None = None,
    ) -> PhaseDiagram:
        """Get a pre-computed phase diagram for a given chemsys.

        For API keys without access to the GNoMe data, its (BY-NC licensed) entries
        are left out, as for all other GNoMe data served to such keys, and the phase
        diagram is rebuilt from the remaining entries, with the energies they would
        have from the GGA(+U)/r2SCAN mixing scheme without the GNoMe entries.

        Arguments:
            chemsys (str): A chemical system (e.g. Li-Fe-O)
            thermo_type (ThermoType): The thermo type for the phase diagram.
                Defaults to ThermoType.GGA_GGA_U_R2SCAN.
            db_version (str | None): Database version of the phase diagram, e.g.
                "2026.04.13" or "latest". Defaults to the rester's version.

        Returns:
            (PhaseDiagram): Pymatgen phase diagram object.
        """
        validated_thermo_type = self._check_thermo_types([thermo_type]).pop()

        sorted_chemsys = "-".join(sorted(chemsys.split("-")))

        # Loading the (large) table and scanning it for one system takes seconds,
        # so show what's happening rather than blocking silently:
        with status(
            f"Fetching the {validated_thermo_type} phase diagram for {sorted_chemsys}...",
            enabled=not self.mute_progress_bars,
        ):
            pd_lbl, _ = self._get_delta_table(
                "materialsproject-build",
                "objects/phase-diagrams",
                label="phase_diagrams",
            )
            requested = _normalize_db_version(db_version) or self.db_version
            if requested == LATEST_DB_VERSION:
                counts = self.delta_catalog.partition_row_counts(pd_lbl) or {}
                version = self._resolve_db_version(requested, counts, "phase-diagrams")
            else:
                version = to_partition_version(requested)

            query = f"""
                SELECT phase_diagram
                FROM   {pd_lbl}
                WHERE  chemsys='{sorted_chemsys}'
                  AND  version='{version}'
                  AND  thermo_type='{validated_thermo_type}'
            """
            table = self._query_delta_single(query, label=pd_lbl)
        as_py = table["phase_diagram"].to_pylist(maps_as_pydicts="strict")

        pd: PhaseDiagram | None = None
        if len(pds := TypeAdapter(list[PhaseDiagramType]).validate_python(as_py)) > 0:
            pd = pds[0]

        # The pre-built phase diagrams include the access-controlled GNoMe entries, which
        # (like their thermo docs, needed e.g. for `get_entries_in_chemsys` with
        # `property_data`) are otherwise not served to API keys without access to them:
        if (
            pd
            and any(e.data.get("license") == "BY-NC" for e in pd.all_entries)
            and not self._has_gnome_access()
        ):
            try:
                accessible = _accessible_entries(pd.all_entries, pd.elements)
                n_left_out = len(pd.all_entries) - len(accessible)
                pd = PhaseDiagram(accessible, elements=pd.elements)
            except ValueError as exc:  # e.g. missing elemental (terminal) entries
                logger.warning(
                    f"Could not rebuild the {sorted_chemsys} phase diagram without its "
                    f"access-controlled (GNoMe) entries, so these are kept: {exc}"
                )
            else:
                logger.info(
                    f"Left out {n_left_out:,} access-controlled (GNoMe) entries from the "
                    f"{sorted_chemsys} phase diagram, as this API key does not have "
                    "access to GNoMe data."
                )

        # Ensure el_ref keys are Element objects for PDPlotter.
        # Ensure qhull_data is a numpy array
        # This should be fixed in pymatgen
        if pd:
            for key, entry in list(pd.el_refs.items()):
                if not isinstance(key, str):
                    break

                pd.el_refs[Element(str(key))] = entry
                pd.el_refs.pop(key)

            if isinstance(pd.qhull_data, list):
                pd.qhull_data = np.array(pd.qhull_data)

        return pd  # type: ignore
