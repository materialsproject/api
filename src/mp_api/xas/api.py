from fastapi import Query, APIRouter
from pymatgen import Element
from mp_api.xas.models import XASDoc, Edge, XASSearchResponse
from maggma.stores import Store
from typing import List
from mp_api.core.utils import formula_to_criteria


def get_router(store: Store):
    router = APIRouter()

    @router.get("/", response_model=List[XASDoc], summary="Get XAS Documents")
    async def get_xas(
        task_id: str = Query(None, title="Material Task ID"),
        edge: Edge = Query(None, title="XAS Edge"),
        # xas_type: XASType = Query(None, title="XAS Spectrum Type", alias="type"),
        absorbing_element: Element = Query(None, title="Absorbing Element"),
        skip: int = Query(0, title="number of XAS spectra to skip"),
        limit: int = Query(
            10, title="Number of XAS spectra to return. This is limited to 500"
        ),
    ):
        store.connect()
        query = {
            "task_id": task_id,
            "edge": edge.value if edge else None,
            "absorbing_element": absorbing_element,
        }
        query = {k: str(v) for k, v in query.items() if v}
        to_return = []

        if int(limit) > 500:
            limit = 500

        for doc in store.query(criteria=query, skip=skip, limit=limit):
            xas_doc = XASDoc.parse_obj(doc)
            to_return.append(xas_doc)

        return to_return

    @router.get(
        "/search", response_model=List[XASSearchResponse], summary="Find XAS Documents"
    )
    async def search_xas(
        edge: Edge = Query(None, title="XAS Edge"),
        absorbing_element: Element = Query(None, title="Absorbing Element"),
        elements: List[Element] = Query(
            None,
            title="Material Elements",
            description="Elements required in the material",
        ),
        formula: str = Query(
            None,
            title="Formula",
            description="Formula of the material with wild-cards, anonymized  or real elements",
        ),
        chemsys: str = Query(
            None, title="Chemical System", description="Chemical system to search in"
        ),
        skip: int = Query(0, title="number of search results to skip"),
        limit: int = Query(
            10, title="Number of search results to return. This is limited to 500"
        ),
    ):
        store.connect()
        query = {
            "edge": edge.value if edge else None,
            "absorbing_element": absorbing_element,
            "chemsys": chemsys,
            "elements": {"$all": [str(e) for e in elements]} if elements else None,
        }

        if formula:
            try:
                query.update(formula_to_criteria(formula))
            except Exception as e:
                print(e)
                # Return HTTP error?

        query = {k: str(v) for k, v in query.items() if v}

        if int(limit) > 500:
            limit = 500

        to_return = [
            XASSearchResponse(
                task_id=d["task_id"],
                edge=d["edge"],
                absorbing_element=d["absorbing_element"],
                formula_pretty=d["formula_pretty"],
            )
            for d in store.query(
                criteria=query,
                properties=["task_id", "edge", "absorbing_element", "formula_pretty"],
                skip=skip,
                limit=limit,
            )
        ]

        return to_return

    @router.get(
        "/count", response_model=int, summary="Count the number of XAS Documents"
    )
    async def count_xas(
        edge: Edge = Query(None, title="XAS Edge"),
        absorbing_element: Element = Query(None, title="Absorbing Element"),
        elements: List[Element] = Query(
            None,
            title="Material Elements",
            description="Elements required in the material",
        ),
        formula: str = Query(
            None,
            title="Formula",
            description="Formula of the material with wild-cards, anonymized  or real elements",
        ),
        chemsys: str = Query(
            None, title="Chemical System", description="Chemical system to search in"
        ),
    ):
        store.connect()
        query = {
            "edge": edge.value if edge else None,
            "absorbing_element": absorbing_element,
            "chemsys": chemsys,
            "elements": {"$all": [str(e) for e in elements]} if elements else None,
        }

        if formula:
            try:
                query.update(formula_to_criteria(formula))
            except Exception as e:
                print(e)
                # Return HTTP error?

        query = {k: str(v) for k, v in query.items() if v}

        return store.count(query)

    @router.get(
        "/elements",
        response_model=List[Element],
        summary="Find elements for documents matching this criteria",
    )
    async def has_elements(
        edge: Edge = Query(None, title="XAS Edge"),
        absorbing_element: Element = Query(None, title="Absorbing Element"),
        elements: List[Element] = Query(
            None,
            title="Material Elements",
            description="Elements required in the material",
        ),
        formula: str = Query(
            None,
            title="Formula",
            description="Formula of the material with wild-cards, anonymized  or real elements",
        ),
        chemsys: str = Query(
            None, title="Chemical System", description="Chemical system to search in"
        ),
    ):
        store.connect()
        query = {
            "edge": edge.value if edge else None,
            "absorbing_element": str(absorbing_element) if absorbing_element else None,
            "chemsys": chemsys,
            "elements": {"$all": [str(e) for e in elements]} if elements else None,
        }

        if formula:
            try:
                query.update(formula_to_criteria(formula))
            except Exception as e:
                print(e)
                # Return HTTP error?

        query = {k: v for k, v in query.items() if v}

        return store.distinct("elements", criteria=query)

    @router.get(
        "/heartbeat",
        response_model=str,
        summary="Heart beat endpoint that should return 'OK'",
    )
    async def hearbeat():
        return "OK"

    return router


# Use environvariables
# mongodb URL  - provided by environment
