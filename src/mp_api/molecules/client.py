from typing import List, Optional, Tuple
from collections import defaultdict
import warnings

from pymatgen.core.periodic_table import Element

from mp_api.core.client import BaseRester, MPRestError
from mp_api.molecules.models import MoleculesDoc


class MoleculesRester(BaseRester):

    suffix = "molecules"
    document_model = MoleculesDoc  # type: ignore

    def get_molecule_from_molecule_id(self, molecule_id: str):
        """
        Get molecule data for a given Materials Project molecule ID.

        Arguments:
            molecule_id (str): Materials project molecule ID

        Returns:
            results (Dict): Dictionary containing molecule data.
        """

        result = self._make_request("{}/?all_fields=true".format(molecule_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")

    def search_molecules_docs(
        self,
        elements: Optional[List[Element]] = None,
        nelements: Optional[Tuple[float, float]] = None,
        EA: Optional[Tuple[float, float]] = None,
        IE: Optional[Tuple[float, float]] = None,
        charge: Optional[Tuple[float, float]] = None,
        pointgroup: Optional[str] = None,
        smiles: Optional[str] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
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
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in SubstratesDoc to return data for.
                Default is the film_id and substrate_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project molecule IDs.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

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

        if fields:
            query_params.update({"fields": ",".join(fields)})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results
