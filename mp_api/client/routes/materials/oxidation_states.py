from __future__ import annotations

from collections import defaultdict

from emmet.core.oxidation_states import OxidationStateDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class OxidationStatesRester(BaseRester[OxidationStateDoc]):
    suffix = "materials/oxidation_states"
    document_model = OxidationStateDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | list[str] | None = None,
        formula: str | list[str] | None = None,
        possible_species: str | list[str] | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query oxidation state docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            possible_species (List[str]): A list of element symbols appended with oxidation states (e.g. [Cr2+, O2-]]).
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in OxidationStateDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([OxidationStateDoc]) List of oxidation state documents
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if possible_species:
            query_params.update({"possible_species": ",".join(possible_species)})

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
            **query_params,
        )
