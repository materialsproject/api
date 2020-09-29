from fastapi import Query
from mp_api.core.query_operator import STORE_PARAMS, QueryOperator
from mp_api.xas.models import Edge, XASType
from pymatgen.core.periodic_table import Element


class XASQuery(QueryOperator):
    def query(
        self,
        edge: Edge = Query(None, title="XAS Edge"),
        spectrum_type: XASType = Query(None, title="Spectrum Type"),
        absorbing_element: Element = Query(None, title="Absorbing Element"),
    ) -> STORE_PARAMS:
        """
        Query parameters unique to XAS
        """
        query = {
            "edge": edge.value if edge else None,
            "absorbing_element": str(absorbing_element) if absorbing_element else None,
        }
        query = {k: v for k, v in query.items() if v}

        return {"criteria": query} if len(query) > 0 else {}
