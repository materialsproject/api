from __future__ import annotations

from typing import TYPE_CHECKING

from emmet.core.symmetry import CrystalSystem
from emmet.core.vasp.calc_types import RunType
from emmet.core.vasp.material import BlessedCalcs, MaterialsDoc
from pymatgen.core.structure import Structure

from mp_api.client.core.client import CoreRester, MPRestError
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS
from mp_api.client.core.utils import validate_ids
from mp_api.client.routes.materials import MATERIALS_RESTERS

if TYPE_CHECKING:
    from typing import Any

    from pymatgen.entries.computed_entries import ComputedStructureEntry


class MaterialsRester(CoreRester):
    suffix = "materials/core"
    document_model = MaterialsDoc  # type: ignore
    primary_key = "material_id"
    _sub_resters = MATERIALS_RESTERS

    def get_structure_by_material_id(
        self, material_id: str, final: bool = True
    ) -> Structure | list[Structure]:
        """Get a structure for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID
            final (bool): Whether to get the final structure, or the list of initial
                (pre-relaxation) structures. Defaults to True.

        Returns:
            structure (Union[Structure, List[Structure]]): Pymatgen structure object or list of
                pymatgen structure objects.
        """
        field = "structure" if final else "initial_structures"

        response = self.search(material_ids=material_id, fields=[field])

        if response and response[0]:
            response = response[0]
            # Ensure that return type is a Structure regardless of `model_dump`
            if isinstance(response[field], dict):
                response[field] = Structure.from_dict(response[field])
            elif isinstance(response[field], list) and any(
                isinstance(struct, dict) for struct in response[field]
            ):
                response[field] = [
                    Structure.from_dict(struct) for struct in response[field]
                ]

        return response[field] if response else response  # type: ignore

    def search(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | list[str] | None = None,
        crystal_system: CrystalSystem | None = None,
        density: tuple[float, float] | None = None,
        deprecated: bool | None = False,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        num_elements: tuple[int, int] | None = None,
        num_sites: tuple[int, int] | None = None,
        spacegroup_number: int | None = None,
        spacegroup_symbol: str | None = None,
        task_ids: list[str] | None = None,
        volume: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[MaterialsDoc] | list[dict]:
        """Query core material docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            crystal_system (CrystalSystem): Crystal system of material.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            num_sites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            task_ids (List[str]): List of Materials Project IDs to return data for.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([MaterialsDoc], [dict]) List of material documents or dictionaries.
        """
        query_params: dict = {"deprecated": deprecated}

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if task_ids:
            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

        query_params.update(
            {
                "crystal_system": crystal_system,
                "spacegroup_number": spacegroup_number,
                "spacegroup_symbol": spacegroup_symbol,
            }
        )

        if num_sites:
            query_params.update(
                {"nsites_min": num_sites[0], "nsites_max": num_sites[1]}
            )

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if volume:
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if density:
            query_params.update({"density_min": density[0], "density_max": density[1]})

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

    def find_structure(
        self,
        filename_or_structure,
        ltol=MAPI_CLIENT_SETTINGS.LTOL,
        stol=MAPI_CLIENT_SETTINGS.STOL,
        angle_tol=MAPI_CLIENT_SETTINGS.ANGLE_TOL,
        allow_multiple_results=False,
    ) -> list[str] | str:
        """Finds matching structures from the Materials Project database.

        Multiple results may be returned of "similar" structures based on
        distance using the pymatgen StructureMatcher algorithm, however only
        a single result should match with the same spacegroup, calculated to the
        default tolerances.

        Args:
            filename_or_structure: filename or Structure object
            ltol: fractional length tolerance
            stol: site tolerance
            angle_tol: angle tolerance in degrees
            allow_multiple_results: changes return type for either
            a single material_id or list of material_ids
        Returns:
            A matching material_id if one is found or list of results if allow_multiple_results
            is True
        Raises:
            MPRestError
        """
        params = {"ltol": ltol, "stol": stol, "angle_tol": angle_tol, "_limit": 1}

        if isinstance(filename_or_structure, str):
            s = Structure.from_file(filename_or_structure)
        elif isinstance(filename_or_structure, Structure):
            s = filename_or_structure
        else:
            raise MPRestError("Provide filename or Structure object.")

        results = self._post_resource(
            body=s.as_dict(),
            params=params,
            suburl="find_structure",
            use_document_model=False,
        ).get("data")

        if not results:
            return []

        material_ids = validate_ids([doc["material_id"] for doc in results])

        if len(material_ids) > 1:  # type: ignore
            if not allow_multiple_results:
                raise ValueError(
                    "Multiple matches found for this combination of tolerances, but "
                    "`allow_multiple_results` set to False."
                )
            return material_ids  # type: ignore

        return material_ids[0]

    def get_blessed_entries(
        self,
        run_type: str | RunType = RunType.r2SCAN,
        material_ids: list[str] | None = None,
        uncorrected_energy: tuple[float | None, float | None] | float | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
    ) -> list[dict[str, str | dict | ComputedStructureEntry]]:
        """Get blessed calculation entries for a given material and run type.

        Args:
            run_type (str or RunType): Calculation run type (e.g. GGA, GGA+U, r2SCAN, PBESol)
            material_ids (list[str]): List of material ID values
            uncorrected_energy (tuple[Optional[float], Optional[float]] | float): Tuple of minimum and maximum uncorrected DFT energy in eV/atom.
                Note that if a single value is passed, it will be used as the minimum and maximum.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.

        Returns:
            list of dict, of the form:
                {
                    "material_id": MPID,
                    "blessed_entry": ComputedStructureEntry
                }
        """
        query_params: dict[str, Any] = {"run_type": str(run_type)}
        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if uncorrected_energy:
            if isinstance(uncorrected_energy, float):
                uncorrected_energy = (uncorrected_energy, uncorrected_energy)

            query_params.update(
                {
                    "energy_min": uncorrected_energy[0],
                    "energy_max": uncorrected_energy[1],
                }
            )

        results = self._query_resource(
            query_params,
            fields=["material_id", "entries"],
            suburl="blessed_tasks",
            parallel_param="material_ids" if material_ids else None,
            chunk_size=chunk_size,
            num_chunks=num_chunks,
        )

        return [
            {
                "material_id": doc["material_id"],
                "blessed_entry": (
                    next(
                        getattr(doc["entries"], k, None)
                        for k in BlessedCalcs.model_fields
                        if getattr(doc["entries"], k, None)
                    )
                    if self.use_document_model
                    else next(
                        doc["entries"][k]
                        for k in BlessedCalcs.model_fields
                        if doc["entries"].get(k)
                    )
                ),
            }
            for doc in (results.get("data") or [])
        ]
