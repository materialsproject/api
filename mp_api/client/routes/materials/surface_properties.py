from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.surface_properties import SurfacePropDoc

from mp_api.client.core import BaseRester


class SurfacePropertiesRester(BaseRester[SurfacePropDoc]):
    suffix = "materials/surface_properties"
    document_model = SurfacePropDoc  # type: ignore
    primary_key = "task_id"

    def search_surface_properties_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.surface_properties.search_surface_properties_docs is deprecated. "
            "Please use MPRester.surface_properties.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        has_reconstructed: bool | None = None,
        shape_factor: tuple[float, float] | None = None,
        surface_energy_anisotropy: tuple[float, float] | None = None,
        weighted_surface_energy: tuple[float, float] | None = None,
        weighted_work_function: tuple[float, float] | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query surface properties docs using a variety of search criteria.

        Arguments:
            has_reconstructed (bool): Whether the entry has any reconstructed surfaces.
            shape_factor (Tuple[float,float]): Minimum and maximum shape factor values to consider.
            surface_energy_anisotropy (Tuple[float,float]): Minimum and maximum surface energy anisotropy values to
                consider.
            weighted_surface_energy (Tuple[float,float]): Minimum and maximum weighted surface energy in J/m² to
                consider.
            weighted_work_function (Tuple[float,float]): Minimum and maximum weighted work function in eV to consider.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
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

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

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
