from typing import List, Optional
from pymatgen import Element
from pymatgen import Structure

from mp_api.core.client import RESTer, RESTError
from mp_api.xas.models import Edge, XASType


class CoreRESTer(RESTer):
    def __init__(self, api_url, **kwargs):
        """
        Initializes the CoreRESTer to a MAPI URL
        """

        self.api_url = api_url.strip("/")

        super().__init__(endpoint=self.api_url + "/core/", **kwargs)

    def get_structure_from_material_id(self, material_id: str):
        query_params = {"fields": ["structure"]}

        result = self._make_request("{}/?fields=structure".format(material_id))

        if len(result.get("data", [])) > 0:
            structure = Structure.from_dict(result["data"][0]["structure"])
            return structure
        else:
            raise RESTError("No document found")
