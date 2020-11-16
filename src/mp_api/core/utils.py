import inspect
from typing import List, Dict, Callable, Any
from typing_extensions import Literal
from importlib import import_module

QUERY_PARAMS = ["criteria", "properties", "sort", "skip", "limit"]
STORE_PARAMS = Dict[Literal["criteria", "properties", "sort", "skip", "limit"], Any]


def dynamic_import(abs_module_path: str, class_name: str):
    """
    Dynamic class importer from: https://www.bnmetrics.com/blog/dynamic-import-in-python3
    """
    module_object = import_module(abs_module_path)
    target_class = getattr(module_object, class_name)
    return target_class


def merge_queries(queries: List[STORE_PARAMS]) -> STORE_PARAMS:

    criteria: STORE_PARAMS = {}
    properties: List[str] = []

    for sub_query in queries:
        if "criteria" in sub_query:
            criteria.update(sub_query["criteria"])
        if "properties" in sub_query:
            properties.extend(sub_query["properties"])

    remainder = {
        k: v
        for query in queries
        for k, v in query.items()
        if k not in ["criteria", "properties"]
    }

    return {
        "criteria": criteria,
        "properties": properties if len(properties) > 0 else None,
        **remainder,
    }


def attach_signature(function: Callable, defaults: Dict, annotations: Dict):
    """
    Attaches signature for defaults and annotations for parameters to function

    Args:
        function: callable function to attach the signature to
        defaults: dictionary of parameters -> default values
        annotations: dictionary of type annoations for the parameters
    """

    required_params = [
        inspect.Parameter(
            param,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=defaults.get(param, None),
            annotation=annotations.get(param, None),
        )
        for param in annotations.keys()
        if param not in defaults.keys()
    ]

    optional_params = [
        inspect.Parameter(
            param,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=defaults.get(param, None),
            annotation=annotations.get(param, None),
        )
        for param in defaults.keys()
    ]

    setattr(
        function, "__signature__", inspect.Signature(required_params + optional_params)
    )
