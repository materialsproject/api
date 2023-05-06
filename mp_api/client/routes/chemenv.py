from collections import defaultdict
from typing import List, Optional, Tuple, Union

from emmet.core.chemenv import (
    ChemEnvDoc,
    COORDINATION_GEOMETRIES,
    COORDINATION_GEOMETRIES_IUPAC,
    COORDINATION_GEOMETRIES_IUCR,
    COORDINATION_GEOMETRIES_NAMES,
)

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ChemenvRester(BaseRester[ChemEnvDoc]):
    suffix = "materials/chemenv"
    document_model = ChemEnvDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: Optional[Union[str, List[str]]] = None,
        chemenv_iucr: Optional[Union[COORDINATION_GEOMETRIES_IUCR, List[COORDINATION_GEOMETRIES_IUCR]]] = None,
        chemenv_iupac: Optional[Union[COORDINATION_GEOMETRIES_IUPAC, List[COORDINATION_GEOMETRIES_IUPAC]]] = None,
        chemenv_name: Optional[Union[COORDINATION_GEOMETRIES_NAMES, List[COORDINATION_GEOMETRIES_NAMES]]] = None,
        chemenv_symbol: Optional[Union[COORDINATION_GEOMETRIES, List[COORDINATION_GEOMETRIES]]] = None,
        csm: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        num_elements: Optional[Tuple[int, int]] = None,
        num_sites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        species: Optional[Union[str, List[str]]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """Query for chemical environment data.

        Arguments:
            material_ids (str, List[str]): Search forchemical environment associated with the specified Material IDs.
            chemenv_iucr (COORDINATION_GEOMETRIES_IUCR, List[COORDINATION_GEOMETRIES_IUCR]): Unique cationic species in IUCR format.
            chemenv_iupac (COORDINATION_GEOMETRIES_IUPAC, List[COORDINATION_GEOMETRIES_IUPAC]): Unique cationic species in IUPAC format.
            chemenv_name (COORDINATION_GEOMETRIES_NAMES, List[COORDINATION_GEOMETRIES_NAMES]): Coordination environment descriptions for unique cationic species.
            chemenv_symbol (COORDINATION_GEOMETRIES, List[COORDINATION_GEOMETRIES]): ChemEnv symbols for unique (cationic) species in structure.
            csm (Tuple[float,float]): Minimum and maximum value of continuous symmetry measure to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            num_sites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            species (str, List[str]): Unique (cationic) species in structure.
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

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if num_sites:
            query_params.update({"nsites_min": num_sites[0], "nsites_max": num_sites[1]})

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update({"nelements_min": num_elements[0], "nelements_max": num_elements[1]})

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        param_map = {
            "chemenv_iucr": (chemenv_iucr, COORDINATION_GEOMETRIES_IUCR),
            "chemenv_iupac": (chemenv_iupac, COORDINATION_GEOMETRIES_IUPAC),
            "chemenv_name": (chemenv_name, COORDINATION_GEOMETRIES_NAMES),
            "chemenv_symbol": (chemenv_symbol, COORDINATION_GEOMETRIES),
        }

        for name, (param, param_type) in param_map.items():
            if param:
                if isinstance(param, str):
                    param = [param]

                valid_types = {*map(str, param_type.__args__)}
                if invalid_types := set(param) - valid_types:
                    raise ValueError(f"Invalid {name}(s) passed: {invalid_types}, valid types are: {valid_types}")

                query_params.update({name: ",".join(param)})

        if species:
            if isinstance(species, str):
                species = [species]

            query_params.update({"species": ",".join(species)})

        if sort_fields:
            query_params.update({"_sort_fields": ",".join([s.strip() for s in sort_fields])})

        query_params = {entry: query_params[entry] for entry in query_params if query_params[entry] is not None}

        return super()._search(
            num_chunks=num_chunks, chunk_size=chunk_size, all_fields=all_fields, fields=fields, **query_params
        )
