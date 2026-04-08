"""Define testing utils that need to imported."""

# pragma: exclude file

from __future__ import annotations

try:
    import pytest
except ImportError as exc:
    raise ImportError(
        "You must `pip install 'mp-api[test]' to use these testing utilities."
    ) from exc

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

requires_api_key = pytest.mark.skipif(
    os.getenv("MP_API_KEY") is None,
    reason="No API key found.",
)

NUM_DOCS = 5


def client_search_testing(
    search_method: Callable,
    excluded_params: list[str],
    alt_name_dict: dict[str, str],
    custom_field_tests: dict[str, Any],
    sub_doc_fields: list[str],
    int_bounds: tuple[int, int] = (-100, 100),
    float_bounds: tuple[float, float] = (-100.12, 100.12),
):
    """Function to test a client using its search method.
    Each parameter is used to query for data, which is then checked.

    Args:
        search_method (Callable): Client search method
        excluded_params (list[str]): List of parameters to exclude from testing
        alt_name_dict (dict[str, str]): Alternative names for parameters used in the projection and subsequent data checking
        custom_field_tests (dict[str, Any]): Custom queries for specific fields.
        sub_doc_fields (list[str]): Prefixes for fields to check in resulting data. Useful when data to be tested is nested.
        int_bounds (tuple[int,int]) : integer bounds to use in testing int-type query arguments
        float_bounds (tuple[float,float]) : float bounds to use in testing float-type query arguments
    """
    if search_method is None:
        return
    # Get list of parameters
    param_tuples = list(search_method.__annotations__.items())

    # Query API for each numeric and boolean parameter and check if returned
    for entry in param_tuples:
        param = entry[0]

        if param not in excluded_params + ["return"]:
            param_type = entry[1]
            q: dict[str, Any] = {"chunk_size": 1, "num_chunks": 1}

            if "tuple[int, int]" in param_type:
                q[param] = int_bounds
            elif "tuple[float, float]" in param_type:
                q[param] = float_bounds
            elif "bool" in param_type:
                q[param] = False
            elif param in custom_field_tests:
                q[param] = custom_field_tests[param]
            else:
                raise ValueError(
                    f"Parameter '{param}' with type '{param_type}' was not "
                    "properly identified in the generic search method test."
                )

            if len(docs := search_method(**q)) > 0:
                doc = docs[0].model_dump()
            else:
                raise ValueError("No documents returned")

            for sub_field in sub_doc_fields:
                if sub_field in doc:
                    doc = doc[sub_field]

            assert doc[alt_name_dict.get(param, param)] is not None


def client_pagination(search_method: Callable, id_name: str):
    page_1 = search_method(_page=1, chunk_size=NUM_DOCS, fields=[id_name])
    page_2 = search_method(_page=2, chunk_size=NUM_DOCS, fields=[id_name])
    assert all(len(results) == NUM_DOCS for results in (page_1, page_2))
    assert {str(getattr(doc, id_name)) for doc in page_1}.intersection(
        {str(getattr(doc, id_name)) for doc in page_2}
    ) == set()


def client_sort(search_method: Callable, sort_fields: str | Sequence[str]):
    for sort_field in [sort_fields] if isinstance(sort_fields, str) else sort_fields:
        asc = search_method(
            _page=1, _sort_fields=sort_field, chunk_size=NUM_DOCS, fields=[sort_field]
        )
        desc = search_method(
            _page=1,
            _sort_fields=f"-{sort_field}",
            chunk_size=NUM_DOCS,
            fields=[sort_field],
        )

        idxs = list(range(NUM_DOCS))
        assert sorted(idxs, key=lambda idx: getattr(asc[idx], sort_field)) == idxs

        assert (
            sorted(
                idxs,
                key=lambda idx: getattr(desc[idx], sort_field),
                reverse=True,
            )
            == idxs
        )
