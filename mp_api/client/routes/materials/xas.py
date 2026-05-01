from __future__ import annotations

from typing import TYPE_CHECKING

from emmet.core.xas import XASDoc
from pymatgen.core.periodic_table import Element

from mp_api.client.core import BaseRester

if TYPE_CHECKING:
    from typing import Any

    from emmet.core.types.enums import XasEdge, XasType


class XASRester(BaseRester):
    suffix = "materials/xas"
    document_model = XASDoc  # type: ignore
    primary_key = "spectrum_id"
    delta_backed = False

    def search(
        self,
        edge: XasEdge | None = None,
        absorbing_element: Element | None = None,
        formula: str | None = None,
        chemsys: str | list[str] | None = None,
        elements: list[str] | None = None,
        material_ids: list[str] | None = None,
        spectrum_type: XasType | None = None,
        spectrum_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
        _page: int | None = None,
        _sort_fields: str | None = None,
    ):
        """Query core XAS docs using a variety of search criteria.

        Arguments:
            edge (XasEdge): The absorption edge (e.g. K, L2, L3, L2,3).
            absorbing_element (Element): The absorbing element.
            formula (str): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            elements (List[str]): A list of elements.
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            spectrum_type (XasType): Spectrum type (e.g. EXAFS, XAFS, or XANES).
            spectrum_ids (str, List[str]): A single Spectrum ID string or list of strings
                (e.g., mp-149-XANES-Li-K, [mp-149-XANES-Li-K, mp-13-XANES-Li-K]).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.
            _page (int or None) : Page of the results to skip to.
            _sort_fields (str or None) : Field to sort on. Including a leading "-" sign will reverse sort order.

        Returns:
            ([MaterialsDoc]) List of material documents
        """
        _locals = locals()
        query_params: dict[str, Any] = {
            k: _locals[k]
            for k in ("edge", "spectrum_type", "formula", "_page", "_sort_fields")
            if _locals.get(k) is not None
        }

        if absorbing_element:
            query_params.update(
                {
                    "absorbing_element": (
                        str(absorbing_element.symbol)
                        if isinstance(absorbing_element, Element)
                        else absorbing_element
                    )
                }
            )
        for k in ("chemsys", "elements", "material_ids", "spectrum_ids"):
            if (v := _locals.get(k)) is not None:
                query_params[k] = ",".join([v] if isinstance(v, str) else v)

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
