from typing import List, Optional, Tuple
from collections import defaultdict

from pymatgen.core.periodic_table import Element

from mp_api.core.client import BaseRester
from emmet.core.molecules_jcesr import MoleculesDoc


class MoleculesRester(BaseRester[MoleculesDoc]):

    suffix = "molecules"
    document_model = MoleculesDoc  # type: ignore
    primary_key = "task_id"

    def search_molecules_docs(
        self,
        elements: Optional[List[Element]] = None,
        nelements: Optional[Tuple[float, float]] = None,
        EA: Optional[Tuple[float, float]] = None,
        IE: Optional[Tuple[float, float]] = None,
        charge: Optional[Tuple[float, float]] = None,
        pointgroup: Optional[str] = None,
        smiles: Optional[str] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            film_orientation (List[Elements]): List of elements that are in the molecule.
            nelements (Tuple[float,float]): Minimum and maximum number of elements in the molecule to consider.
            EA (Tuple[float,float]): Minimum and maximum value of the electron affinity in eV to consider.
            IE (Tuple[float,float]): Minimum and maximum value of the ionization energy in eV to consider.
            charge (Tuple[float,float]): Minimum and maximum value of the charge in +e to consider.
            pointgroup (str): Point group of the molecule in Schoenflies notation.
            smiles (str): The simplified molecular input line-entry system (SMILES) representation of the molecule.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MoleculesDoc to return data for.
                Default is the material_id only if all_fields is False.

        Returns:
            ([MoleculesDoc]) List of molecule documents
        """

        query_params = defaultdict(dict)  # type: dict

        if elements:
            query_params.update({"elements": ",".join([str(ele) for ele in elements])})

        if pointgroup:
            query_params.update({"pointgroup": pointgroup})

        if smiles:
            query_params.update({"smiles": smiles})

        if nelements:
            query_params.update(
                {"nelements_min": nelements[0], "nelements_max": nelements[1]}
            )

        if EA:
            query_params.update({"EA_min": EA[0], "EA_max": EA[1]})

        if IE:
            query_params.update({"IE_min": IE[0], "IE_max": IE[1]})

        if charge:
            query_params.update({"charge_min": charge[0], "charge_max": charge[1]})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

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
