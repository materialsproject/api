from typing import List, Optional
from pymatgen import Element
from mp_api.core.client import BaseRester, MPRestError
from mp_api.xas.models import Edge, XASType


class XASRESTer(BaseRester):
    def __init__(self, api_url, **kwargs):
        """
        Initializes the XASRester to a MAPI URL
        """

        self.api_url = api_url.strip("/")

        super().__init__(endpoint=self.api_url + "/xas/", **kwargs)

    def get_available_elements(
        self,
        edge: Optional[Edge] = None,
        spectrum_type: Optional[XASType] = None,
        absorbing_element: Optional[Element] = None,
        required_elements: Optional[List[Element]] = None,
    ):
        return [str(e) for e in Element]

    def get_xas_doc(self, xas_id: str):
        # TODO do some checking here for sub-components
        query_params = {"xas_id": xas_id, "all_fields": True}

        result = self.query(query_params)
        if len(result.get("data", [])) > 0:
            return result["data"][0]
        else:
            raise MPRestError("No document found")

    def search_xas_docs(
        self,
        edge: Optional[Edge] = None,
        absorbing_element: Optional[Element] = None,
        required_elements: Optional[List[Element]] = None,
        formula: Optional[str] = None,
        skip: Optional[int] = 0,
        limit: Optional[int] = 10,
        fields: Optional[List[str]] = None,
    ):
        query_params = {
            "edge": str(edge.value) if edge else None,
            "absorbing_element": str(absorbing_element) if absorbing_element else None,
            "formula": formula,
            "skip": skip,
            "limit": limit,
        }

        if required_elements:
            query_params["elements"] = ",".join([str(el) for el in required_elements])

        if fields is not None:
            query_params["fields"] = ",".join(fields)

        result = self.query(query_params)
        return result.get("data", [])

    def count_xas_docs(
        self,
        edge: Optional[Edge] = None,
        absorbing_element: Optional[Element] = None,
        required_elements: Optional[List[Element]] = None,
        formula: Optional[str] = None,
    ):
        query_params = {
            "edge": str(edge.value) if edge else None,
            "absorbing_element": str(absorbing_element) if absorbing_element else None,
            "formula": formula,
        }

        if required_elements:
            query_params["elements"] = ",".join([str(el) for el in required_elements])

        query_params["limit"] = "1"
        result = self.query(query_params)
        return result.get("meta", {}).get("total", 0)
