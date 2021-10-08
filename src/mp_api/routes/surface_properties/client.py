from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.routes.surface_properties.models import SurfacePropDoc


class SurfacePropertiesRester(BaseRester[SurfacePropDoc]):

    suffix = "surface_properties"
    document_model = SurfacePropDoc  # type: ignore
    primary_key = "task_id"

    def search_surface_properties_docs(
        self,
        weighted_surface_energy: Optional[Tuple[float, float]] = None,
        weighted_work_function: Optional[Tuple[float, float]] = None,
        surface_energy_anisotropy: Optional[Tuple[float, float]] = None,
        shape_factor: Optional[Tuple[float, float]] = None,
        has_reconstructed: Optional[bool] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
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
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SurfacePropDoc to return data for.
                Default is material_id only if all_fields is False.

        Returns:
            ([SurfacePropDoc]) List of surface properties documents
        """

        query_params = defaultdict(dict)  # type: dict

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

        if has_reconstructed is not None:
            query_params.update({"has_reconstructed": has_reconstructed})

        if sort_field:
            query_params.update({"sort_field": sort_field})

        if ascending is not None:
            query_params.update({"ascending": ascending})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
