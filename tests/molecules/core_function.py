from __future__ import annotations
from typing import Callable, Any


def client_search_testing(
    search_method: Callable,
    excluded_params: list[str],
    alt_name_dict: dict[str, str],
    custom_field_tests: dict[str, Any],
    sub_doc_fields: list[str],
):
    """
    Function to test a client using its search method.
    Each parameter is used to query for data, which is then checked.

    Args:
        search_method (Callable): Client search method
        excluded_params (list[str]): List of parameters to exclude from testing
        alt_name_dict (dict[str, str]): Alternative names for parameters used in the projection and subsequent data checking
        custom_field_tests (dict[str, Any]): Custom queries for specific fields.
        sub_doc_fields (list[str]): Prefixes for fields to check in resulting data. Useful when data to be tested is nested.
    """
    if search_method is not None:
        # Get list of parameters
        param_tuples = list(search_method.__annotations__.items())
        # Query API for each numeric and boolean parameter and check if returned
        for entry in param_tuples:
            param = entry[0]
            if param not in excluded_params:
                param_type = entry[1]
                q = None

                if param in custom_field_tests:
                    q = {
                        param: custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif "tuple[int, int]" in param_type:
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif "tuple[float, float]" in param_type:
                    q = {
                        param: (-3000.12, 3000.12),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is bool:
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }

                docs = search_method(**q)

                if len(docs) > 0:
                    doc = docs[0].model_dump()
                else:
                    raise ValueError("No documents returned")

                assert doc[alt_name_dict.get(param, param)] is not None
