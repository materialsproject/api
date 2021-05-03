import inspect
from typing import List, Dict, Callable, Any, Optional, Type
from typing_extensions import Literal
from importlib import import_module

from monty.json import MSONable
from pydantic.utils import lenient_issubclass
from pydantic.schema import get_flat_models_from_model
from pydantic import BaseModel

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


def api_sanitize(
    pydantic_model: Type[BaseModel],
    fields_to_leave: Optional[List[str]] = None,
    allow_dict_msonable=False,
):
    """
    Function to clean up pydantic models for the API by:
        1.) Making fields optional
        2.) Allowing dictionaries in-place of the objects for MSONable quantities

    WARNING: This works in place, so it mutates the model and all sub-models

    Args:
        fields_to_leave: list of strings for model fields as "model__name__.field"
    """

    models = [
        model
        for model in get_flat_models_from_model(pydantic_model)
        if lenient_issubclass(model, BaseModel)
    ]

    fields_to_leave = fields_to_leave or []
    fields_tuples = [f.split(".") for f in fields_to_leave]
    assert all(len(f) == 2 for f in fields_tuples)

    for model in models:
        model_fields_to_leave = {f[1] for f in fields_tuples if model.__name__ == f[0]}
        for name, field in model.__fields__.items():  # type: ignore
            field_type = field.type_

            if name not in model_fields_to_leave:
                field.required = False
                field.field_info.default = None

            if (
                field_type is not None
                and lenient_issubclass(field_type, MSONable)
                and allow_dict_msonable
            ):
                field.type_ = allow_msonable_dict(field_type)
                field.populate_validators()

    return pydantic_model


def allow_msonable_dict(monty_cls: Type[MSONable]):
    """
    Patch Monty to allow for dict values for MSONable
    """

    def validate_monty(cls, v):
        """
        Stub validator for MSONable as a dictionary only
        """
        if isinstance(v, cls):
            return v
        elif isinstance(v, dict):
            # Just validate the simple Monty Dict Model
            errors = []
            if v.get("@module", "") != monty_cls.__module__:
                errors.append("@module")

            if v.get("@class", "") != monty_cls.__name__:
                errors.append("@class")

            if len(errors) > 0:
                raise ValueError(
                    "Missing Monty seriailzation fields in dictionary: {errors}"
                )

            return v
        else:
            raise ValueError(f"Must provide {cls.__name__} or MSONable dictionary")

    setattr(monty_cls, "validate_monty", classmethod(validate_monty))

    return monty_cls
