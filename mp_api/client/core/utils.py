import re
from typing import List, Optional, Type, get_args

from monty.json import MSONable
from pydantic import BaseModel
from pydantic.schema import get_flat_models_from_model
from pydantic.utils import lenient_issubclass


def validate_ids(id_list: List[str]):
    """Function to validate material and task IDs.

    Args:
        id_list (List[str]): List of material or task IDs.

    Raises:
        ValueError: If at least one ID is not formatted correctly.

    Returns:
        id_list: Returns original ID list if everything is formatted correctly.
    """
    pattern = "(mp|mvc|mol|mpcule)-.*"

    for entry in id_list:
        if re.match(pattern, entry) is None:
            raise ValueError(f"{entry} is not formatted correctly!")

    return id_list


def api_sanitize(
    pydantic_model: Type[BaseModel],
    fields_to_leave: Optional[List[str]] = None,
    allow_dict_msonable=False,
):
    """Function to clean up pydantic models for the API by:
        1.) Making fields optional
        2.) Allowing dictionaries in-place of the objects for MSONable quantities.

    WARNING: This works in place, so it mutates the model and all sub-models

    Args:
        fields_to_leave: list of strings for model fields as "model__name__.field"
    """
    models = [
        model for model in get_flat_models_from_model(pydantic_model) if issubclass(model, BaseModel)
    ]  # type: List[Type[BaseModel]]

    fields_to_leave = fields_to_leave or []
    fields_tuples = [f.split(".") for f in fields_to_leave]
    assert all(len(f) == 2 for f in fields_tuples)

    for model in models:
        model_fields_to_leave = {f[1] for f in fields_tuples if model.__name__ == f[0]}
        for name, field in model.__fields__.items():
            field_type = field.type_

            if name not in model_fields_to_leave:
                field.required = False
                field.default = None
                field.default_factory = None
                field.allow_none = True
                field.field_info.default = None
                field.field_info.default_factory = None

            if field_type is not None and allow_dict_msonable:
                if lenient_issubclass(field_type, MSONable):
                    field.type_ = allow_msonable_dict(field_type)
                else:
                    for sub_type in get_args(field_type):
                        if lenient_issubclass(sub_type, MSONable):
                            allow_msonable_dict(sub_type)
                field.populate_validators()

    return pydantic_model


def allow_msonable_dict(monty_cls: Type[MSONable]):
    """Patch Monty to allow for dict values for MSONable."""

    def validate_monty(cls, v):
        """Stub validator for MSONable as a dictionary only."""
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
                raise ValueError("Missing Monty seriailzation fields in dictionary: {errors}")

            return v
        else:
            raise ValueError(f"Must provide {cls.__name__} or MSONable dictionary")

    monty_cls.validate_monty = classmethod(validate_monty)

    return monty_cls


def jsanitize(obj, strict=False, allow_bson=False):
    """
    This method cleans an input json-like object, either a list or a dict or
    some sequence, nested or otherwise, by converting all non-string
    dictionary keys (such as int and float) to strings, and also recursively
    encodes all objects using Monty's as_dict() protocol.
    Args:
        obj: input json-like object.
        strict (bool): This parameters sets the behavior when jsanitize
            encounters an object it does not understand. If strict is True,
            jsanitize will try to get the as_dict() attribute of the object. If
            no such attribute is found, an attribute error will be thrown. If
            strict is False, jsanitize will simply call str(object) to convert
            the object to a string representation.
        allow_bson (bool): This parameters sets the behavior when jsanitize
            encounters an bson supported type such as objectid and datetime. If
            True, such bson types will be ignored, allowing for proper
            insertion into MongoDb databases.
    Returns:
        Sanitized dict that can be json serialized.
    """
    if allow_bson and (
        isinstance(obj, (datetime.datetime, bytes)) or (bson is not None and isinstance(obj, bson.objectid.ObjectId))
    ):
        return obj

    if isinstance(obj, (list, tuple, set)):
        return [jsanitize(i, strict=strict, allow_bson=allow_bson) for i in obj]
    if np is not None and isinstance(obj, np.ndarray):
        return [jsanitize(i, strict=strict, allow_bson=allow_bson) for i in obj.tolist()]
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k.__str__(): jsanitize(v, strict=strict, allow_bson=allow_bson) for k, v in obj.items()}
    if isinstance(obj, MSONable):
        return {k.__str__(): jsanitize(v, strict=strict, allow_bson=allow_bson) for k, v in obj.as_dict().items()}

    if isinstance(obj, BaseModel):
        return {k.__str__(): jsanitize(v, strict=strict, allow_bson=allow_bson) for k, v in obj.dict().items()}
    if isinstance(obj, (int, float)):
        if np.isnan(obj):
            return 0
        return obj

    if obj is None:
        return None

    if not strict:
        return obj.__str__()

    if isinstance(obj, str):
        return obj.__str__()

    return jsanitize(obj.as_dict(), strict=strict, allow_bson=allow_bson)
