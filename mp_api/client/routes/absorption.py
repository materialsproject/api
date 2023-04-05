from typing import List, Optional, Union
from collections import defaultdict

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids
from emmet.core.absorption import AbsorptionDoc


class AbsorptionRester(BaseRester[AbsorptionDoc]):

    suffix = "absorption"
    document_model = AbsorptionDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: Optional[Union[str, List[str]]] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        formula: Optional[List[str]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ) -> List[AbsorptionDoc]:
        """
        Query for optical absorption spectra data.

        Arguments:
            material_ids (str, List[str]): Search for optical absorption data associated with the specified Material IDs
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in AbsorptionDoc to return data for.

        Returns:
            ([AbsorptionDoc]) List of optical absorption documents.
        """

        query_params = defaultdict(dict)  # type: dict

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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
            formulae=formula,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
