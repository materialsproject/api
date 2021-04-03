from typing import Iterable, List, Optional
import warnings

from mp_api.tasks.models import TaskDoc
from mp_api.core.client import BaseRester, MPRestError


class TaskRester(BaseRester):

    suffix = "tasks"
    document_model = TaskDoc

    def get_trajectory(self, task_id):
        """
        Returns a Trajectory object containing the geometry of the
        material throughout a calculation. This is most useful for
        observing how a material relaxes during a geometry optimization.

        :param task_id: A specified task_id
        :return: Trajectory object
        """

        pass

    def is_deprecated(self, task_id):
        """
        Returns whether or not a given task is deprecated.
        :param task_id: A specified task_id
        :return: True or False
        """

        pass

    def search_task_docs(
        self,
        chemsys_formula: Optional[str] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
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
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs reduced chemical formulas, and last updated tags.
        """

        query_params = {}  # type: dict

        if chunk_size <= 0:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if fields:
            query_params.update({"fields": ",".join(fields)})

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self._query_resource(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            for result in results:
                yield result
