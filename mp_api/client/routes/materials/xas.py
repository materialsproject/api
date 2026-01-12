from __future__ import annotations

from typing import TYPE_CHECKING

from emmet.core.xas import XASDoc
from pymatgen.core.periodic_table import Element

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids

if TYPE_CHECKING:
    from emmet.core.types.enums import XasEdge, XasType


class XASRester(BaseRester):
    suffix = "materials/xas"
    document_model = XASDoc  # type: ignore
    primary_key = "spectrum_id"

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

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if spectrum_ids:
            if isinstance(spectrum_ids, str):
                spectrum_ids = [spectrum_ids]

            query_params.update({"spectrum_ids": ",".join(spectrum_ids)})

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
