from mp_api.core.client import RESTer, RESTError


class SimilarityRESTer(RESTer):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the CoreRESTer to a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/similarity/", **kwargs)

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
            raise RESTError("No document found")
