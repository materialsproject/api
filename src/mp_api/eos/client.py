from typing import List, Optional, Tuple

from mp_api.core.client import RESTer, RESTError


class EOSRESTer(RESTer):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the CoreRESTer to a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/eos/", **kwargs)

    def get_eos_from_material_id(self, material_id: str, version: Optional[str] = None):
        """
        Get equations of state data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID
            
        Returns:
            eos_data (Dict): Dictionary containing equations of state data.
        """
        if version is None:
            result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise RESTError("No document found")

    def search_eos_docs(
        self,
        volume: Optional[Tuple[float, float]] = (None, None),
        energy: Optional[Tuple[float, float]] = (None, None),
        num_chunks: Optional[int] = None,
        chunk_size: Optional[int] = 100,
        fields: Optional[List[str]] = [None],
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            volume (Tuple[float,float]): Minimum and maximum volume in A³/atom to consider for EOS plot range.
            energy (Tuple[float,float]): Minimum and maximum energy in eV/atom to consider for EOS plot range.
            deprecated (bool): Whether the material is tagged as deprecated.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'. 
                Defaults to Materials Project IDs only.
        """

        query_params = {}

        if any(volume):
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if any(energy):
            query_params.update({"energy_min": emergy[0], "energy_max": energy[1]})

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

