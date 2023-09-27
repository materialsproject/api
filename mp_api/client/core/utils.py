from __future__ import annotations

import re
from functools import cache
from typing import Optional, get_args

from maggma.utils import get_flat_models_from_model
from monty.json import MSONable
from pydantic import BaseModel
from pydantic._internal._utils import lenient_issubclass
from pydantic.fields import FieldInfo


def validate_ids(id_list: list[str]):
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


@cache
def api_sanitize(
    pydantic_model: BaseModel,
    fields_to_leave: list[str] | None = None,
    allow_dict_msonable=False,
):
    """Function to clean up pydantic models for the API by:
        1.) Making fields optional
        2.) Allowing dictionaries in-place of the objects for MSONable quantities.

    WARNING: This works in place, so it mutates the model and all sub-models

    Args:
        pydantic_model (BaseModel): Pydantic model to alter
        fields_to_leave (list[str] | None): list of strings for model fields as "model__name__.field".
            Defaults to None.
        allow_dict_msonable (bool): Whether to allow dictionaries in place of MSONable quantities.
            Defaults to False
    """
    models = [
        model
        for model in get_flat_models_from_model(pydantic_model)
        if issubclass(model, BaseModel)
    ]  # type: list[BaseModel]

    fields_to_leave = fields_to_leave or []
    fields_tuples = [f.split(".") for f in fields_to_leave]
    assert all(len(f) == 2 for f in fields_tuples)

    for model in models:
        model_fields_to_leave = {f[1] for f in fields_tuples if model.__name__ == f[0]}
        for name in model.model_fields:
            field = model.model_fields[name]
            field_type = field.annotation

            if field_type is not None and allow_dict_msonable:
                if lenient_issubclass(field_type, MSONable):
                    field_type = allow_msonable_dict(field_type)
                else:
                    for sub_type in get_args(field_type):
                        if lenient_issubclass(sub_type, MSONable):
                            allow_msonable_dict(sub_type)

            if name not in model_fields_to_leave:
                new_field = FieldInfo.from_annotated_attribute(
                    Optional[field_type], None
                )
                model.model_fields[name] = new_field

        model.model_rebuild(force=True)

    return pydantic_model


def allow_msonable_dict(monty_cls: type[MSONable]):
    """Patch Monty to allow for dict values for MSONable."""

    def validate_monty(cls, v, _):
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
                raise ValueError(
                    "Missing Monty seriailzation fields in dictionary: {errors}"
                )

            return v
        else:
            raise ValueError(f"Must provide {cls.__name__} or MSONable dictionary")

    monty_cls.validate_monty_v2 = classmethod(validate_monty)

    return monty_cls
