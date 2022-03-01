from typing import List, Optional, Union

from emmet.core.tasks import TaskDoc
from mp_api.core.client import BaseRester, MPRestError


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
        :return: List of trajectory objects
        """

        traj_data = self._query_resource_data(
            suburl=f"trajectory/{task_id}/", use_document_model=False
        )[0].get("trajectories", None)

        if traj_data is None:
            raise MPRestError(f"No trajectory data for {task_id} found")

        return traj_data

    def search_task_docs(
        self,
        formula: Optional[str] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core task docs using a variety of search criteria.

        Arguments:
            formula (str): A formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk. Max size is 100.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in TaskDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([TaskDoc]) List of task documents
        """

        query_params = {}  # type: dict

        if formula:
            query_params.update({"formula": formula})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
