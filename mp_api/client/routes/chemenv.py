from collections import defaultdict
from typing import List, Optional, Tuple, Union

from emmet.core.chemenv import ChemEnvDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ChemenvRester(BaseRester[ChemEnvDoc]):
    suffix = "materials/chemenv"
    document_model = ChemEnvDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: Optional[Union[str, List[str]]] = None,
        chemenv_iucr: Optional[Union[str, List[str]]] = None,
        chemenv_iupac: Optional[Union[str, List[str]]] = None,
        chemenv_name: Optional[Union[str, List[str]]] = None,
        csm: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        num_elements: Optional[Tuple[int, int]] = None,
        num_sites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ) -> List[ChemEnvDoc]:
        """Query for chemical environment data.

        Arguments:
            material_ids (str, List[str]): Search forchemical environment associated with the specified Material IDs.
            chemenv_iucr (str, List[str]): Unique cationic species in IUCR format.
            chemenv_iupac (str, List[str]): Unique cationic species in IUPAC format.
            chemenv_iupac (str, List[str]): Coordination environment descriptions for unique cationic species.
            density (Tuple[float,float]): Minimum and maximum value of continuous symmetry measure to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            num_sites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ChemEnvDoc to return data for.

        Returns:
            ([ChemEnvDoc]) List of chemenv documents.
        """
        query_params = defaultdict(dict)  # type: dict

        if csm:
            query_params.update({"csm_min": csm[0], "csm_max": csm[1]})

        if volume:
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if density:
            query_params.update({"density_min": density[0], "density_max": density[1]})

        if num_sites:
            query_params.update(
                {"nsites_min": num_sites[0], "nsites_max": num_sites[1]}
            )

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if chemenv_iucr:
            if isinstance(chemenv_iucr, str):
                chemenv_iucr = [chemenv_iucr]

            query_params.update({"chemenv_iucr": ",".join(chemenv_iucr)})

        if chemenv_iupac:
            if isinstance(chemenv_iupac, str):
                chemenv_iupac = [chemenv_iupac]

            query_params.update({"chemenv_iupac": ",".join(chemenv_iupac)})

        if chemenv_name:
            if isinstance(chemenv_name, str):
                chemenv_name = [chemenv_name]

            query_params.update({"chemenv_name": ",".join(chemenv_name)})

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
            **query_params
        )
