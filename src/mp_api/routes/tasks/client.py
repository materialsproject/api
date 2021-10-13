from typing import List, Optional

from mp_api.routes.tasks.models import TaskDoc
from mp_api.core.client import BaseRester


class TaskRester(BaseRester[TaskDoc]):

    suffix = "tasks"
    document_model = TaskDoc  # type: ignore
    primary_key = "task_id"

    def get_trajectory(self, task_id):
        """
        Returns a Trajectory object containing the geometry of the
        material throughout a calculation. This is most useful for
        observing how a material relaxes during a geometry optimization.

        :param task_id: A specified task_id
        :return: Trajectory object
        """

        pass

    def search_task_docs(
        self,
        chemsys_formula: Optional[str] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core task docs using a variety of search criteria.

        Arguments:
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk. Max size is 100.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in TaskDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([TaskDoc]) List of task documents
        """

        query_params = {}  # type: dict

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
