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
                if "tuple[int, int]" in param_type:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif "tuple[float, float]" in param_type:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100.12, 100.12),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif "bool" in param_type:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param in custom_field_tests:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }

                doc = search_method(**q)[0].model_dump()

                for sub_field in sub_doc_fields:
                    if sub_field in doc:
                        doc = doc[sub_field]

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )
