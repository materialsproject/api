from typing import List, Optional
from pymatgen import Element
from mp_api.core.client import RESTer
from mp_api.xas.models import Edge


class XASRESTer(RESTer):
    def get_available_elements(
        self,
        edge: Optional[Edge] = None,
        absorbing_element: Optional[Element] = None,
        required_elements: Optional[List[Element]] = None,
    ):

        query_string = ""
        query_string += f"edge={edge.value}," if edge else ""
        query_string += (
            f"absorbing_element={str(absorbing_element)}," if absorbing_element else ""
        )
        query_string += (
            ",".join([f"elements={str(el)}" for el in required_elements])
            if required_elements
            else ""
        )

        url = (
            f"/xas/elements?{query_string}"
            if len(query_string) > 0
            else "/xas/elements"
        )

        data = self._make_request(url)

        return data

