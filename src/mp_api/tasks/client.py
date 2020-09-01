from typing import List, Optional, Tuple
from pymatgen import Structure

from mp_api.core.client import RESTer, RESTError
from mp_api.materials.models.core import CrystalSystem


class TaskRESTer(RESTer):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the TaskRESTer to a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/tasks/", **kwargs)

    def search_task_docs(
        self,
        chemsys_formula: Optional[str] = None,
        task_id: Optional[str] = [None],
        num_chunks: Optional[int] = None,
        chunk_size: Optional[int] = 100,
        fields: Optional[List[str]] = [None],
    ):
        """
        Query core task docs using a variety of search criteria.

        Arguments:
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            task_id (str): Single Materials Project ID to return data for.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'. 
                Defaults to Materials Project IDs reduced chemical formulas, and last updated tags.
        """

        query_params = {}

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if task_id:
            query_params.update({"task_id": task_id})

        if any(fields):
            query_params.update({"fields": ",".join(fields)})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results
