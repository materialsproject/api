from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.summary import HasProps, SummaryDoc
from emmet.core.symmetry import CrystalSystem
from pymatgen.analysis.magnetism import Ordering

from mp_api.client.core import BaseRester, MPRestError, MPRestWarning
from mp_api.client.core.utils import validate_ids


class SummaryRester(BaseRester):
    suffix = "materials/summary"
    document_model = SummaryDoc  # type: ignore
    primary_key = "material_id"

    def search(  # noqa: D417
        self,
        band_gap: tuple[float, float] | None = None,
        chemsys: str | list[str] | None = None,
        crystal_system: CrystalSystem | None = None,
        density: tuple[float, float] | None = None,
        deprecated: bool | None = None,
        e_electronic: tuple[float, float] | None = None,
        e_ionic: tuple[float, float] | None = None,
        e_total: tuple[float, float] | None = None,
        efermi: tuple[float, float] | None = None,
        elastic_anisotropy: tuple[float, float] | None = None,
        elements: list[str] | None = None,
        energy_above_hull: tuple[float, float] | None = None,
        equilibrium_reaction_energy: tuple[float, float] | None = None,
        exclude_elements: list[str] | None = None,
        formation_energy: tuple[float, float] | None = None,
        formula: str | list[str] | None = None,
        g_reuss: tuple[float, float] | None = None,
        g_voigt: tuple[float, float] | None = None,
        g_vrh: tuple[float, float] | None = None,
        has_props: list[HasProps] | list[str] | None = None,
        has_reconstructed: bool | None = None,
        is_gap_direct: bool | None = None,
        is_metal: bool | None = None,
        is_stable: bool | None = None,
        k_reuss: tuple[float, float] | None = None,
        k_voigt: tuple[float, float] | None = None,
        k_vrh: tuple[float, float] | None = None,
        magnetic_ordering: Ordering | None = None,
        material_ids: str | list[str] | None = None,
        n: tuple[float, float] | None = None,
        num_elements: int | tuple[int, int] | None = None,
        num_sites: int | tuple[int, int] | None = None,
        num_magnetic_sites: tuple[int, int] | None = None,
        num_unique_magnetic_sites: tuple[int, int] | None = None,
        piezoelectric_modulus: tuple[float, float] | None = None,
        poisson_ratio: tuple[float, float] | None = None,
        possible_species: list[str] | None = None,
        shape_factor: tuple[float, float] | None = None,
        spacegroup_number: int | list[int] | None = None,
        spacegroup_symbol: str | list[str] | None = None,
        surface_energy_anisotropy: tuple[float, float] | None = None,
        theoretical: bool | None = None,
        total_energy: tuple[float, float] | None = None,
        total_magnetization: tuple[float, float] | None = None,
        total_magnetization_normalized_formula_units: tuple[float, float] | None = None,
        total_magnetization_normalized_vol: tuple[float, float] | None = None,
        uncorrected_energy: tuple[float, float] | None = None,
        volume: tuple[float, float] | None = None,
        weighted_surface_energy: tuple[float, float] | None = None,
        weighted_work_function: tuple[float, float] | None = None,
        include_gnome: bool = True,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
        **kwargs,
    ) -> list[SummaryDoc] | list[dict]:
        """Query core data using a variety of search criteria.

        Arguments:
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            crystal_system (CrystalSystem or list[CrystalSystem]): Crystal system(s) of the materials.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            e_electronic (Tuple[float,float]): Minimum and maximum electronic dielectric constant to consider.
            e_ionic (Tuple[float,float]): Minimum and maximum ionic dielectric constant to consider.
            e_total (Tuple[float,float]): Minimum and maximum total dielectric constant to consider.
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            elastic_anisotropy (Tuple[float,float]): Minimum and maximum value to consider for the elastic anisotropy.
            elements (List[str]): A list of elements.
            energy_above_hull (Tuple[int,int]): Minimum and maximum energy above the hull in eV/atom to consider.
            equilibrium_reaction_energy (Tuple[float,float]): Minimum and maximum equilibrium reaction energy in
                eV/atom to consider.
            exclude_elements (List(str)): List of elements to exclude.
            formation_energy (Tuple[int,int]): Minimum and maximum formation energy in eV/atom to consider.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            g_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for the Reuss average
                of the shear modulus.
            g_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for the Voigt average
                of the shear modulus.
            g_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for the Voigt-Reuss-Hill
                average of the shear modulus.
            has_props: (List[HasProps], List[str]): The calculated properties available for the material.
            has_reconstructed (bool): Whether the entry has any reconstructed surfaces.
            is_gap_direct (bool): Whether the material has a direct band gap.
            is_metal (bool): Whether the material is considered a metal.
            is_stable (bool): Whether the material lies on the convex energy hull.
            k_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for the Reuss average
                of the bulk modulus.
            k_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for the Voigt average
                of the bulk modulus.
            k_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for the Voigt-Reuss-Hill
                average of the bulk modulus.
            magnetic_ordering (Ordering): Magnetic ordering of the material.
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            n (Tuple[float,float]): Minimum and maximum refractive index to consider.
            nelements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            num_elements (Tuple[int,int]): Alias for `nelements`, deprecated. Minimum and maximum number of elements to consider.
            num_sites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            num_magnetic_sites (Tuple[int,int]): Minimum and maximum number of magnetic sites to consider.
            num_unique_magnetic_sites (Tuple[int,int]): Minimum and maximum number of unique magnetic sites to consider.
            piezoelectric_modulus (Tuple[float,float]): Minimum and maximum piezoelectric modulus to consider.
            poisson_ratio (Tuple[float,float]): Minimum and maximum value to consider for Poisson's ratio.
            possible_species (List(str)): List of element symbols appended with oxidation states. (e.g. Cr2+,O2-)
            shape_factor (Tuple[float,float]): Minimum and maximum shape factor values to consider.
            spacegroup_number (int or list[int]): Space group number(s) of materials.
            spacegroup_symbol (str or list[str]): Space group symbol(s) of the materials in international short symbol notation.
            surface_energy_anisotropy (Tuple[float,float]): Minimum and maximum surface energy anisotropy values
                to consider.
            theoretical: (bool): Whether the material is theoretical.
            total_energy (Tuple[int,int]): Minimum and maximum corrected total energy in eV/atom to consider.
            total_magnetization (Tuple[float,float]): Minimum and maximum total magnetization values to consider.
            total_magnetization_normalized_formula_units (Tuple[float,float]): Minimum and maximum total magnetization
                values normalized by formula units to consider.
            total_magnetization_normalized_vol (Tuple[float,float]): Minimum and maximum total magnetization values
                normalized by volume to consider.
            uncorrected_energy (Tuple[int,int]): Minimum and maximum uncorrected total energy in eV/atom to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            weighted_surface_energy (Tuple[float,float]): Minimum and maximum weighted surface energy
                in J/m² to consider.
            weighted_work_function (Tuple[float,float]): Minimum and maximum weighted work function in eV to consider.
            include_gnome (bool): whether to include materials from GNoMe dataset
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SummaryDoc to return data for.
                Default is material_id if all_fields is False.

        Returns:
            ([SummaryDoc], [dict]) List of SummaryDoc documents or dictionaries.
        """
        query_params: dict = defaultdict(dict)

        not_aliased_kwargs = [
            "energy_above_hull",
            "nsites",
            "volume",
            "density",
            "band_gap",
            "efermi",
            "total_magnetization",
            "total_magnetization_normalized_vol",
            "total_magnetization_normalized_formula_units",
            "num_magnetic_sites",
            "num_unique_magnetic_sites",
            "k_voigt",
            "k_reuss",
            "k_vrh",
            "g_voigt",
            "g_reuss",
            "g_vrh",
            "e_total",
            "e_ionic",
            "e_electronic",
            "n",
            "weighted_surface_energy",
            "weighted_work_function",
            "shape_factor",
        ]

        min_max_name_dict = {
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "uncorrected_energy": "uncorrected_energy_per_atom",
            "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
            "elastic_anisotropy": "universal_anisotropy",
            "poisson_ratio": "homogeneous_poisson",
            "num_sites": "nsites",
            "num_elements": "nelements",
            "piezoelectric_modulus": "e_ij_max",
            "surface_energy_anisotropy": "surface_anisotropy",
        }

        min_max_name_dict.update({k: k for k in not_aliased_kwargs})
        mmnd_inv = {v: k for k, v in min_max_name_dict.items() if k != v}

        # Set user query params from `locals`
        user_settings = {
            k: v for k, v in locals().items() if k in min_max_name_dict and v
        }

        # Check to see if user specified _search fields using **kwargs,
        # or if any of the **kwargs are unparsable
        db_keys = {k: [] for k in ("duplicate", "warn", "unknown")}
        for k, v in kwargs.items():
            category = "unknown"
            if non_db_k := mmnd_inv.get(k):
                if user_settings.get(non_db_k):
                    # Both a search and _search equivalent field are specified
                    category = "duplicate"
                elif v:
                    # Only the _search field is specified
                    category = "warn"
                    user_settings[non_db_k] = v
            db_keys[category].append(non_db_k or k)

        # If any _search or unknown fields were set, throw warnings/exceptions
        if any(db_keys.values()):
            warning_strs: list[str] = []
            exc_strs: list[str] = []

            def csrc(x):
                return f"\x1b[34m{x}\x1b[39m"

            def _csrc(x):
                return f"\x1b[31m{x}\x1b[39m"

            # Warn the user if they input any fields from _search without setting equivalent kwargs in search
            if db_keys["warn"]:
                warning_strs.extend(
                    [
                        f"You have specified fields used by {_csrc('`_search`')} that can be understood by {csrc('`search`')}",
                        f"   {', '.join([_csrc(min_max_name_dict[k]) for k in db_keys['warn']])}",
                        f"To ensure long term support, please use their {csrc('`search`')} equivalents:",
                        f"   {', '.join([csrc(k) for k in db_keys['warn']])}",
                    ]
                )

            # Throw an exception if the user input a field from _search and its equivalent search kwarg
            if db_keys["duplicate"]:
                dupe_pairs = "\n".join(
                    f"{csrc(k)} and {_csrc(min_max_name_dict[k])}"
                    for k in db_keys["duplicate"]
                )
                exc_strs.extend(
                    [
                        f"You have specified fields known to both {csrc('`search`')} and {_csrc('`_search`')}",
                        f"   {dupe_pairs}",
                        f"To avoid query ambiguity, please check your {csrc('`search`')} query and only specify",
                        f"   {', '.join([csrc(k) for k in db_keys['duplicate']])}",
                    ]
                )
            # Throw an exception if any unknown kwargs were input
            if db_keys["unknown"]:
                exc_strs.extend(
                    [
                        f"You have specified the following kwargs which are unknown to {csrc('`search`')}, "
                        f"but may be known to {_csrc('`_search`')}",
                        f"    \x1b[36m{', '.join(db_keys['unknown'])}\x1b[39m",
                    ]
                )

            # Always print links to documentation on warning / exception
            warn_ref_strs = [
                "Please see the documentation:",
                f"    {csrc('`search`: https://materialsproject.github.io/api/_autosummary/mp_api.client.routes.materials.summary.SummaryRester.html#mp_api.client.routes.materials.summary.SummaryRester.search')}",
                f"   {_csrc('`_search`: https://api.materialsproject.org/redoc#tag/Materials-Summary/operation/search_materials_summary__get')}",
            ]

            if exc_strs:
                raise MPRestError("\n".join([*warning_strs, *exc_strs, *warn_ref_strs]))
            if warn_ref_strs:
                warnings.warn(
                    "\n".join([*warning_strs, *warn_ref_strs]), category=MPRestWarning
                )

        for param, value in user_settings.items():
            if isinstance(value, (int, float)):
                value = (value, value)
            query_params.update(
                {
                    f"{min_max_name_dict[param]}_min": value[0],
                    f"{min_max_name_dict[param]}_max": value[1],
                }
            )

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if deprecated is not None:
            query_params.update({"deprecated": deprecated})

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements is not None:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if possible_species is not None:
            query_params.update({"possible_species": ",".join(possible_species)})

        symm_cardinality = {
            "crystal_system": 7,
            "spacegroup_number": 230,
            "spacegroup_symbol": 230,
        }
        for k, cardinality in symm_cardinality.items():
            if hasattr(symm_vals := locals().get(k), "__len__") and not isinstance(
                symm_vals, str
            ):
                if len(symm_vals) < cardinality // 2:
                    query_params.update({k: ",".join(str(v) for v in symm_vals)})
                else:
                    raise ValueError(
                        f"Querying `{k}` by a list of values is only "
                        f"supported for up to {cardinality//2 - 1} values. "
                        f"For your query, retrieve all data first and then filter on `{k}`."
                    )
            else:
                query_params.update({k: symm_vals})

        if is_stable is not None:
            query_params.update({"is_stable": is_stable})

        if is_gap_direct is not None:
            query_params.update({"is_gap_direct": is_gap_direct})

        if is_metal is not None:
            query_params.update({"is_metal": is_metal})

        if magnetic_ordering:
            query_params.update({"ordering": magnetic_ordering.value})

        if has_reconstructed is not None:
            query_params.update({"has_reconstructed": has_reconstructed})

        if has_props:
            has_props_clean = []
            for prop in has_props:
                try:
                    has_props_clean.append(HasProps(prop).value)
                except ValueError:
                    raise MPRestError(f"'{prop}' is not a valid property.")

            query_params.update({"has_props": ",".join(has_props_clean)})

        if theoretical is not None:
            query_params.update({"theoretical": theoretical})

        if not include_gnome:
            query_params.update({"batch_id_not_eq": "gnome_r2scan_statics"})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
