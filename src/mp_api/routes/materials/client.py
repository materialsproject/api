from typing import List, Optional, Tuple
from pymatgen.core.structure import Structure

from emmet.core.material import MaterialsDoc
from emmet.core.symmetry import CrystalSystem

from mp_api.core.client import BaseRester, MPRestError


class MaterialsRester(BaseRester):

    suffix = "materials"
    document_model = MaterialsDoc  # type: ignore
    supports_versions = True
    primary_key = "material_id"

    def get_structure_by_material_id(self, material_id: str, version: Optional[str] = None) -> Structure:
        """
        Get a structure for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID
            version (str): Version of data to query on in the format 'YYYY.MM.DD'.
                Defaults to None which will return data from the most recent database release.


        Returns:
            structure (Structure): Pymatgen structure object
        """
        return self.get_document_by_id(material_id, fields=["structure"]).structure

    def search_material_docs(
        self,
        version: Optional[str] = None,
        chemsys_formula: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
        crystal_system: Optional[CrystalSystem] = None,
        spacegroup_number: Optional[int] = None,
        spacegroup_symbol: Optional[str] = None,
        nsites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        deprecated: Optional[bool] = False,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            version (str): Version of data to query on in the format 'YYYY.MM.DD'. Defaults to None which will
                return data from the most recent database release.
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            task_ids (List[str]): List of Materials Project IDs to return data for.
            crystal_system (CrystalSystem): Crystal system of material.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([MaterialsDoc]) List of material documents
        """

        query_params = {"deprecated": deprecated}  # type: dict

        if version:
            query_params.update({"version": version})

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if task_ids:
            query_params.update({"task_ids": ",".join(task_ids)})

        query_params.update(
            {
                "crystal_system": crystal_system,
                "spacegroup_number": spacegroup_number,
                "spacegroup_symbol": spacegroup_symbol,
            }
        )

        if nsites:
            query_params.update({"nsites_min": nsites[0], "nsites_max": nsites[1]})

        if volume:
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if density:
            query_params.update({"density_min": density[0], "density_max": density[1]})

        query_params = {entry: query_params[entry] for entry in query_params if query_params[entry] is not None}

        return super().search(
            version=self.version,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )

    def get_database_versions(self):
        """
        Get version tags available for the Materials Project core materials data.
        These can be used to request data from previous releases.

        Returns:
            versions (List[str]): List of database versions as strings.
        """

        result = self._make_request("versions")

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No data found")

    def find_structure(self, filename_or_structure, ltol=0.2, stol=0.3, angle_tol=5):
        """
        Finds matching structures on the Materials Project site.
        Args:
            filename_or_structure: filename or Structure object
        Returns:
            A list of matching materials project ids for structure, \
                including normalized rms distances and max distances between paired sites.
        Raises:
            MPRestError
        """

        params = {"ltol": ltol, "stol": stol, "angle_tol": angle_tol}

        if isinstance(filename_or_structure, str):
            s = Structure.from_file(filename_or_structure)
        elif isinstance(filename_or_structure, Structure):
            s = filename_or_structure
        else:
            raise MPRestError("Provide filename or Structure object.")

        return self._post_resource(
            data=s.as_dict(), params=params, suburl="find_structure", use_document_model=False,
        ).get("data")
