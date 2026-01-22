from __future__ import annotations

from collections import defaultdict

from emmet.core.surface_properties import SurfacePropDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class SurfacePropertiesRester(BaseRester):
    suffix = "materials/surface_properties"
    document_model = SurfacePropDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        has_reconstructed: bool | None = None,
        shape_factor: tuple[float, float] | None = None,
        surface_energy_anisotropy: tuple[float, float] | None = None,
        weighted_surface_energy: tuple[float, float] | None = None,
        weighted_work_function: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[SurfacePropDoc] | list[dict]:
        """Query surface properties docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            has_reconstructed (bool): Whether the entry has any reconstructed surfaces.
            shape_factor (Tuple[float,float]): Minimum and maximum shape factor values to consider.
            surface_energy_anisotropy (Tuple[float,float]): Minimum and maximum surface energy anisotropy values to
                consider.
            weighted_surface_energy (Tuple[float,float]): Minimum and maximum weighted surface energy in J/m² to
                consider.
            weighted_work_function (Tuple[float,float]): Minimum and maximum weighted work function in eV to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SurfacePropDoc to return data for.
                Default is material_id only if all_fields is False.

        Returns:
            ([SurfacePropDoc], [dict]) List of surface properties documents
        """
        query_params: dict = defaultdict(dict)

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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
