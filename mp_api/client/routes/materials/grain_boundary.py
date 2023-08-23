from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.grain_boundary import GBTypeEnum, GrainBoundaryDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class GrainBoundaryRester(BaseRester[GrainBoundaryDoc]):
    suffix = "materials/grain_boundary"
    document_model = GrainBoundaryDoc  # type: ignore
    primary_key = "task_id"

    def search_grain_boundary_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.grain_boundary.search_grain_boundary_docs is deprecated. "
            "Please use MPRester.grain_boundary.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        chemsys: str | None = None,
        gb_plane: list[str] | None = None,
        gb_energy: tuple[float, float] | None = None,
        material_ids: list[str] | None = None,
        pretty_formula: str | None = None,
        rotation_axis: list[str] | None = None,
        rotation_angle: tuple[float, float] | None = None,
        separation_energy: tuple[float, float] | None = None,
        sigma: int | None = None,
        type: GBTypeEnum | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query grain boundary docs using a variety of search criteria.

        Arguments:
             chemsys (str): Dash-delimited string of elements in the material.
             gb_plane(List[str]): The Miller index of grain boundary plane. e.g., [1, 1, 1]
             gb_energy (Tuple[float,float]): Minimum and maximum grain boundary energy in J/m³ to consider.
             material_ids (List[str]): List of Materials Project IDs to query with.
             pretty_formula (str): Formula of the material.
             rotation_angle (Tuple[float,float]): Minimum and maximum rotation angle in degrees to consider.
             rotation_axis(List[str]): The Miller index of rotation axis. e.g., [1, 0, 0], [1, 1, 0], and [1, 1, 1]
                 sigma (int): Sigma value of grain boundary.
             separation_energy (Tuple[float,float]): Minimum and maximum work of separation energy in J/m³ to consider.
             sigma (int): Sigma value of the boundary.
             type (GBTypeEnum): Grain boundary type.
             sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
             num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
             chunk_size (int): Number of data entries per chunk.
             all_fields (bool): Whether to return all fields in the document. Defaults to True.
             fields (List[str]): List of fields in GrainBoundaryDoc to return data for.
                 Default is material_id and last_updated if all_fields is False.

        Returns:
             ([GrainBoundaryDoc]) List of grain boundary documents
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            query_params.update({"task_ids": ",".join(validate_ids(material_ids))})

        if gb_plane:
            query_params.update({"gb_plane": ",".join([str(n) for n in gb_plane])})

        if gb_energy:
            query_params.update(
                {"gb_energy_min": gb_energy[0], "gb_energy_max": gb_energy[1]}
            )

        if separation_energy:
            query_params.update(
                {"w_sep_min": separation_energy[0], "w_sep_max": separation_energy[1]}
            )

        if rotation_angle:
            query_params.update(
                {
                    "rotation_angle_min": rotation_angle[0],
                    "rotation_angle_max": rotation_angle[1],
                }
            )

        if rotation_axis:
            query_params.update(
                {"rotation_axis": ",".join([str(n) for n in rotation_axis])}
            )

        if sigma:
            query_params.update({"sigma": sigma})

        if type:
            query_params.update({"type": type.value})

        if chemsys:
            query_params.update({"chemsys": chemsys})

        if pretty_formula:
            query_params.update({"pretty_formula": pretty_formula})

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
