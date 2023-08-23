from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.bonds import BondingDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class BondsRester(BaseRester[BondingDoc]):
    suffix = "materials/bonds"
    document_model = BondingDoc  # type: ignore
    primary_key = "material_id"

    def search_bonds_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.bonds.search_bonds_docs is deprecated. Please use MPRester.bonds.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        material_ids: str | list[str] | None = None,
        coordination_envs: list[str] | None = None,
        coordination_envs_anonymous: list[str] | None = None,
        max_bond_length: tuple[float, float] | None = None,
        mean_bond_length: tuple[float, float] | None = None,
        min_bond_length: tuple[float, float] | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query bonding docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): Search for bonding data for the specified Material IDs
            coordination_envs (List[str]): List of coordination environments to consider (e.g. ['Mo-S(6)', 'S-Mo(3)']).
            coordination_envs_anonymous (List[str]): List of anonymous coordination environments to consider
                 (e.g. ['A-B(6)', 'A-B(3)']).
            max_bond_length (Tuple[float,float]): Minimum and maximum value for the maximum bond length
                in the structure to consider.
            mean_bond_length (Tuple[float,float]):  Minimum and maximum value for the mean bond length
                in the structure to consider.
            min_bond_length (Tuple[float,float]): Minimum and maximum value for the minimum bond length
                in the structure to consider.
            sort_fields (List[str]): Fields used to sort results. Prefixing with '-' will sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in DielectricDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([BondingDoc]) List of bonding documents.
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if max_bond_length:
            query_params.update(
                {
                    "max_bond_length_min": max_bond_length[0],
                    "max_bond_length_max": max_bond_length[1],
                }
            )

        if min_bond_length:
            query_params.update(
                {
                    "min_bond_length_min": min_bond_length[0],
                    "min_bond_length_max": min_bond_length[1],
                }
            )

        if mean_bond_length:
            query_params.update(
                {
                    "mean_bond_length_min": mean_bond_length[0],
                    "mean_bond_length_max": mean_bond_length[1],
                }
            )

        if coordination_envs is not None:
            query_params.update({"coordination_envs": ",".join(coordination_envs)})

        if coordination_envs_anonymous is not None:
            query_params.update(
                {"coordination_envs_anonymous": ",".join(coordination_envs_anonymous)}
            )

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
