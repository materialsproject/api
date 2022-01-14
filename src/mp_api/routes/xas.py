from typing import List, Optional, Union

from emmet.core.xas import Edge, XASDoc
from mp_api.core.client import BaseRester
from pymatgen.core.periodic_table import Element


class XASRester(BaseRester[XASDoc]):

    suffix = "xas"
    document_model = XASDoc  # type: ignore
    primary_key = "spectrum_id"

    def search_xas_docs(
        self,
        edge: Optional[Edge] = None,
        absorbing_element: Optional[Element] = None,
        formula: Optional[str] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        elements: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core XAS docs using a variety of search criteria.

        Arguments:
            edge (Edge): The absorption edge (e.g. K, L2, L3, L2,3).
            formula (str): A formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            elements (List[str]): A list of elements.
            task_ids (List[str]): List of Materials Project IDs to return data for.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([MaterialsDoc]) List of material documents
        """
        query_params = {}

        if edge:
            query_params.update({"edge": str(edge.value)})

        if absorbing_element:
            query_params.update({"absorbing_element": str(absorbing_element.symbol)})

        if formula:
            query_params.update({"formula": formula})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if task_ids is not None:
            query_params["task_ids"] = ",".join(task_ids)

        if sort_fields:
            query_params.update(
                {"sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
