from __future__ import annotations

import warnings

from emmet.core.xas import Edge, Type, XASDoc
from pymatgen.core.periodic_table import Element

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class XASRester(BaseRester[XASDoc]):
    suffix = "materials/xas"
    document_model = XASDoc  # type: ignore
    primary_key = "spectrum_id"

    def search_xas_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.xas.search_xas_docs is deprecated. "
            "Please use MPRester.xas.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        edge: Edge | None = None,
        absorbing_element: Element | None = None,
        formula: str | None = None,
        chemsys: str | list[str] | None = None,
        elements: list[str] | None = None,
        material_ids: list[str] | None = None,
        spectrum_type: Type | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query core XAS docs using a variety of search criteria.

        Arguments:
            edge (Edge): The absorption edge (e.g. K, L2, L3, L2,3).
            absorbing_element (Element): The absorbing element.
            formula (str): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            elements (List[str]): A list of elements.
            material_ids (List[str]): List of Materials Project IDs to return data for.
            spectrum_type (Type): Spectrum type (e.g. EXAFS, XAFS, or XANES).
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
            query_params.update({"edge": edge})

        if absorbing_element:
            query_params.update(
                {
                    "absorbing_element": str(absorbing_element.symbol)
                    if type(absorbing_element) == Element
                    else absorbing_element
                }
            )

        if spectrum_type:
            query_params.update({"spectrum_type": spectrum_type})

        if formula:
            query_params.update({"formula": formula})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if material_ids is not None:
            query_params["material_ids"] = ",".join(validate_ids(material_ids))

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
