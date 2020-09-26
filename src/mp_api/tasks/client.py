from typing import List, Optional

from mp_api.core.client import BaseRester, MPRestError


class TaskRESTer(BaseRester):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the TaskRESTer with a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/tasks/", **kwargs)

    def get_task_from_material_id(
        self,
        material_id: str,
        fields: List[str] = ["task_id", "formula_pretty", "last_updated"],
    ):
        """
        Get task document data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            data (dict): Task doc data for keys in fields. Defaults to
                task_id, formula_pretty, and last_updated.
        """
        field_vals = ",".join(fields)
        result = self._make_request("{}/?fields={}".format(material_id, field_vals))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")

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
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs reduced chemical formulas, and last updated tags.
        """

        query_params = {}  # type: dict

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if fields:
            query_params.update({"fields": ",".join(fields)})

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results
