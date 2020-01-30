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

        query_params = []
        if edge:
            query_params.append(f"edge={edge.value}")

        if absorbing_element:
            query_params.append(f"absorbing_element={str(absorbing_element)}")
        if required_elements:
            query_params.append(
                "&".join([f"elements={str(el)}" for el in required_elements])
            )

        query_string = "&".join(query_params)

        url = f"elements?{query_string}" if len(query_string) > 0 else "/elements"

        return self._make_request(url)

    def get_xas_doc(self, task_id: str, edge: Edge, absorbing_element: Element):

        query_string = f"?task_id={task_id}&edge={edge.value}&absorbing_element={str(absorbing_element)}"

        return self._make_request(query_string)

    def search_xas_docs(
        self,
        edge: Optional[Edge] = None,
        absorbing_element: Optional[Element] = None,
        required_elements: Optional[List[Element]] = None,
        formula: Optional[str] = None,
        chemsys: Optional[str] = None,
        skip: Optional[PositiveInt] = 0,
        limit: Optional[PositiveInt] = 10,
    ):
        query_params = {
            "edge": f"{edge.value}" if edge else None,
            "absorbing_element": f"{str(absorbing_element)}"
            if absorbing_element
            else None,
            "elements": "&".join([f"elements={str(el)}" for el in required_elements])
            if required_elements
            else None,
            "formula": formula,
            "chemsys": chemsys,
            "skip": skip,
            "limit": limit,
        }

        query_params = {k: v for k, v in query_params.items() if v is not None}

        query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])

        return self._make_request(f"search?{query_string}")

