from typing import List, Optional, Tuple
from collections import defaultdict
import warnings

from mp_api.core.client import BaseRester, MPRestError
from mp_api.surface_properties.models import SurfacePropDoc


class SurfacePropertiesRester(BaseRester):

    suffix = "surface_properties"
    document_model = SurfacePropDoc

    def get_surface_properties_from_material_id(self, material_id: str):
        """
        Get surface properties data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing surface properties data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")

    def search_surface_properties_docs(
        self,
        weighted_surface_energy: Optional[Tuple[float, float]] = None,
        weighted_work_function: Optional[Tuple[float, float]] = None,
        surface_energy_anisotropy: Optional[Tuple[float, float]] = None,
        shape_factor: Optional[Tuple[float, float]] = None,
        has_reconstructed: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query surface properties docs using a variety of search criteria.

        Arguments:
            weighted_surface_energy (Tuple[float,float]): Minimum and maximum weighted surface energy in J/m² to
                consider.
            weighted_work_function (Tuple[float,float]): Minimum and maximum weighted work function in eV to consider.
            surface_energy_anisotropy (Tuple[float,float]): Minimum and maximum surface energy anisotropy values to
                consider.
            shape_factor (Tuple[float,float]): Minimum and maximum shape factor values to consider.
            has_reconstructed (bool): Whether the entry has any reconstructed surfaces.
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

        if weighted_surface_energy:
            query_params.update(
                {
                    "weighted_surface_energy_min": weighted_surface_energy[0],
                    "weighted_surface_energy_max": weighted_surface_energy[1],
                }
            )

        if weighted_work_function:
            query_params.update(
                {
                    "weighted_work_function_min": weighted_work_function[0],
                    "weighted_work_function_max": weighted_work_function[1],
                }
            )

        if surface_energy_anisotropy:
            query_params.update(
                {
                    "surface_anisotropy_min": surface_energy_anisotropy[0],
                    "surface_anisotropy_max": surface_energy_anisotropy[1],
                }
            )

        if shape_factor:
            query_params.update(
                {
                    "shape_factor_min": shape_factor[0],
                    "shape_factor_max": shape_factor[1],
                }
            )

        if has_reconstructed:
            query_params.update({"has_reconstructed": has_reconstructed})

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
