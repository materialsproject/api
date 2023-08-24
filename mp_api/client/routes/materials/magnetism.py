from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.magnetism import MagnetismDoc
from pymatgen.analysis.magnetism import Ordering

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class MagnetismRester(BaseRester[MagnetismDoc]):
    suffix = "materials/magnetism"
    document_model = MagnetismDoc  # type: ignore
    primary_key = "material_id"

    def search_magnetism_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.magnetism.search_magnetism_docs is deprecated. "
            "Please use MPRester.magnetism.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        material_ids: str | list[str] | None = None,
        num_magnetic_sites: tuple[int, int] | None = None,
        num_unique_magnetic_sites: tuple[int, int] | None = None,
        ordering: Ordering | None = None,
        total_magnetization: tuple[float, float] | None = None,
        total_magnetization_normalized_vol: tuple[float, float] | None = None,
        total_magnetization_normalized_formula_units: tuple[float, float] | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query magnetism docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            num_magnetic_sites (Tuple[int,int]): Minimum and maximum number of magnetic sites to consider.
            num_unique_magnetic_sites (Tuple[int,int]): Minimum and maximum number of unique magnetic sites
                to consider.
            ordering (Ordering]): The magnetic ordering of the material.
            total_magnetization (Tuple[float,float]): Minimum and maximum total magnetization values to consider.
            total_magnetization_normalized_vol (Tuple[float,float]): Minimum and maximum total magnetization values
                normalized by volume to consider.
            total_magnetization_normalized_formula_units (Tuple[float,float]): Minimum and maximum total magnetization
                values normalized by formula units to consider.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MagnetismDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([MagnetismDoc]) List of magnetism documents
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if total_magnetization:
            query_params.update(
                {
                    "total_magnetization_min": total_magnetization[0],
                    "total_magnetization_max": total_magnetization[1],
                }
            )

        if total_magnetization_normalized_vol:
            query_params.update(
                {
                    "total_magnetization_normalized_vol_min": total_magnetization_normalized_vol[
                        0
                    ],
                    "total_magnetization_normalized_vol_max": total_magnetization_normalized_vol[
                        1
                    ],
                }
            )

        if total_magnetization_normalized_formula_units:
            query_params.update(
                {
                    "total_magnetization_normalized_formula_units_min": total_magnetization_normalized_formula_units[
                        0
                    ],
                    "total_magnetization_normalized_formula_units_max": total_magnetization_normalized_formula_units[
                        1
                    ],
                }
            )

        if num_magnetic_sites:
            query_params.update(
                {
                    "num_magnetic_sites_min": num_magnetic_sites[0],
                    "num_magnetic_sites_max": num_magnetic_sites[1],
                }
            )

        if num_unique_magnetic_sites:
            query_params.update(
                {
                    "num_unique_magnetic_sites_min": num_unique_magnetic_sites[0],
                    "num_unique_magnetic_sites_max": num_unique_magnetic_sites[1],
                }
            )

        if ordering:
            query_params.update({"ordering": ordering.value})

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
