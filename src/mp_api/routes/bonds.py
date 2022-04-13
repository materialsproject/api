from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from emmet.core.bonds import BondingDoc


class BondsRester(BaseRester[BondingDoc]):

    suffix = "bonds"
    document_model = BondingDoc  # type: ignore
    primary_key = "material_id"

    def search_bonds_docs(
        self,
        max_bond_length: Optional[Tuple[float, float]] = None,
        min_bond_length: Optional[Tuple[float, float]] = None,
        mean_bond_length: Optional[Tuple[float, float]] = None,
        coordination_envs: Optional[List[str]] = None,
        coordination_envs_anonymous: Optional[List[str]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query bonding docs using a variety of search criteria.

        Arguments:
            max_bond_length (Tuple[float,float]): Minimum and maximum value for the maximum bond length
                in the structure to consider.
            min_bond_length (Tuple[float,float]): Minimum and maximum value for the minimum bond length
                in the structure to consider.
            mean_bond_length (Tuple[float,float]):  Minimum and maximum value for the mean bond length
                in the structure to consider.
            coordination_envs (List[str]): List of coordination environments to consider (e.g. ['Mo-S(6)', 'S-Mo(3)']).
            coordination_envs_anonymous (List[str]): List of anonymous coordination environments to consider
                 (e.g. ['A-B(6)', 'A-B(3)']).
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

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
