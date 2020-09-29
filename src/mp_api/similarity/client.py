from mp_api.core.client import BaseRester, MPRestError


class SimilarityRester(BaseRester):

    suffix = "similarity"

    def get_similar_structures(self, material_id: str):
        """
        Get similar structures for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing structure similarity data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")
