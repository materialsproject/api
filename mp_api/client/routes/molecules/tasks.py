from __future__ import annotations

from emmet.core.qchem.task import TaskDocument

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class MoleculesTaskRester(BaseRester[TaskDocument]):
    suffix = "molecules/tasks"
    document_model = TaskDocument
    primary_key = "task_id"

    # TODO: get_trajectory method (once PR in pymatgen)

    def search(
        self,
        task_ids: list[str] | None = None,
        chemsys: str | list[str] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query core task docs using a variety of search criteria.

        Arguments:
            task_ids (List[str]): List of Materials Project IDs to return data for.
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., C-H-O, [C-Li-O, Li-O]).
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): An alphabetical formula (e.g. "C1 Li2 O3" or ["C2 H4", "C2 H6"]).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk. Max size is 100.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in TaskDocument to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([TaskDocument]) List of task documents
        """
        query_params = {}  # type: dict

        if task_ids:
            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

        if formula:
            query_params.update({"formula": formula})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
