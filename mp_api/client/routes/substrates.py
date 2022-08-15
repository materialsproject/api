from typing import List, Optional, Tuple
from collections import defaultdict
import warnings

from mp_api.client.core import BaseRester
from emmet.core.substrates import SubstratesDoc


class SubstratesRester(BaseRester[SubstratesDoc]):

    suffix = "substrates"
    document_model = SubstratesDoc  # type: ignore
    primary_key = "film_id"

    def search_substrates_docs(self, *args, **kwargs):  # pragma: no cover
        """
        Deprecated
        """

        warnings.warn(
            "MPRester.substrates.search_substrates_docs is deprecated. "
            "Please use MPRester.substrates.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        area: Optional[Tuple[float, float]] = None,
        energy: Optional[Tuple[float, float]] = None,
        film_id: Optional[str] = None,
        film_orientation: Optional[List[int]] = None,
        substrate_id: Optional[str] = None,
        substrate_formula: Optional[str] = None,
        substrate_orientation: Optional[List[int]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            area (Tuple[float,float]): Minimum and maximum volume in Å² to consider for the minimim coincident
                interface area range.
            energy (Tuple[float,float]): Minimum and maximum energy in meV to consider for the elastic energy range.
            film_id (str): Materials Project ID of the film material.
            film_orientation (List[int]): Vector indicating the surface orientation of the film material.
            substrate_id (str): Materials Project ID of the substrate material.
            substrate_formula (str): Reduced formula of the substrate material.
            substrate_orientation (List[int]): Vector indicating the surface orientation of the substrate material.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SubstratesDoc to return data for.
                Default is the film_id and substrate_id only if all_fields is False.

        Returns:
            ([SubstratesDoc]) List of substrate documents
        """

        query_params = defaultdict(dict)  # type: dict

        if film_id:
            query_params.update({"film_id": film_id})

        if substrate_id:
            query_params.update({"sub_id": substrate_id})

        if substrate_formula:
            query_params.update({"sub_form": substrate_formula})

        if film_orientation:
            query_params.update(
                {"film_orientation": ",".join([str(i) for i in film_orientation])}
            )

        if substrate_orientation:
            query_params.update(
                {
                    "substrate_orientation": ",".join(
                        [str(i) for i in substrate_orientation]
                    )
                }
            )

        if area:
            query_params.update({"area_min": area[0], "area_max": area[1]})

        if energy:
            query_params.update({"energy_min": energy[0], "energy_max": energy[1]})

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
            **query_params,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )
