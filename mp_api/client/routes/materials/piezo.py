from __future__ import annotations

from collections import defaultdict

from emmet.core.polar import PiezoelectricDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class PiezoRester(BaseRester):
    suffix = "materials/piezoelectric"
    document_model = PiezoelectricDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        piezoelectric_modulus: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[PiezoelectricDoc] | list[dict]:
        """Query piezoelectric data using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            piezoelectric_modulus (Tuple[float,float]): Minimum and maximum of the
                piezoelectric modulus in C/m² to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in PiezoDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([PiezoDoc], [dict]) List of piezoelectric documents
        """
        query_params: dict = defaultdict(dict)

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if piezoelectric_modulus:
            query_params.update(
                {
                    "piezo_modulus_min": piezoelectric_modulus[0],
                    "piezo_modulus_max": piezoelectric_modulus[1],
                }
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
