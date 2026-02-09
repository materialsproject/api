from __future__ import annotations

from collections import defaultdict

from emmet.core.absorption import AbsorptionDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class AbsorptionRester(BaseRester):
    suffix = "materials/absorption"
    document_model = AbsorptionDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        num_sites: int | tuple[int, int] | None = None,
        num_elements: int | tuple[int, int] | None = None,
        volume: float | tuple[float, float] | None = None,
        density: float | tuple[float, float] | None = None,
        band_gap: float | tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[AbsorptionDoc] | list[dict]:
        """Query for optical absorption spectra data.

        Arguments:
            material_ids (str, List[str]):
                Search for optical absorption data associated with the
                specified Material ID(s)
            num_sites (int, tuple[int, int]):
                Search with a single number or a range of number of sites
                in the structure.
            num_elements (int, tuple[int, int]):
                Search with a single number or a range of number of distinct
                elements in the structure.
            volume (float, tuple[float, float]):
                Search with a single number or a range of structural
                (lattice) volumes in Å³.
                If a single number, an uncertainty of ±0.01 is automatically used.
            density (float, tuple[float, float]):
                Search with a single number or a range of structural
                (lattice) densities, in g/cm³.
                If a single number, an uncertainty of ±0.01 is automatically used.
            band_gap (float, tuple[float, float]):
                Search with a single number or a range of band gaps in eV.
                If a single number, an uncertainty of ±0.01 is automatically used.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in AbsorptionDoc to return data for.

        Returns:
            ([AbsorptionDoc], [dict]) List of optical absorption documents or dictionaries.
        """
        query_params: dict = defaultdict(dict)

        aliased = {
            "num_sites": "nsites",
            "num_elements": "nelements",
            "band_gap": "bandgap",
        }
        user_query = locals()
        for k in ("num_sites", "num_elements", "volume", "density", "band_gap"):
            if (value := user_query.get(k)) is not None:
                if k in ("num_sites", "num_elements") and isinstance(value, int):
                    value = (value, value)
                elif k in ("volume", "density", "band_gap") and isinstance(
                    value, int | float
                ):
                    value = (value - 1e-2, value + 1e-2)

                query_params.update(
                    {
                        f"{aliased.get(k,k)}_min": value[0],
                        f"{aliased.get(k,k)}_max": value[1],
                    }
                )

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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
