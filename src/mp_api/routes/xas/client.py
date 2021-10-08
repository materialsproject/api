from typing import List, Optional
from pymatgen.core.periodic_table import Element
from mp_api.core.client import BaseRester, MPRestError
from emmet.core.xas import Edge, Type, XASDoc


class XASRester(BaseRester[XASDoc]):

    suffix = "xas"
    document_model = XASDoc  # type: ignore
    primary_key = "spectrum_id"

    def search_xas_docs(
        # TODO: add proper docstring
        self,
        edge: Optional[Edge] = None,
        absorbing_element: Optional[Element] = None,
        required_elements: Optional[List[Element]] = None,
        formula: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        query_params = {
            "edge": str(edge.value) if edge else None,
            "absorbing_element": str(absorbing_element) if absorbing_element else None,
            "formula": formula,
        }  # type: dict

        if task_ids is not None:
            query_params["task_ids"] = ",".join(task_ids)

        if required_elements:
            query_params["elements"] = ",".join([str(el) for el in required_elements])

        if sort_field:
            query_params.update({"sort_field": sort_field})

        if ascending is not None:
            query_params.update({"ascending": ascending})

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
