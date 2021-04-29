from datetime import datetime
from typing import Generic, List, Optional, TypeVar, Type
from monty.json import MSONable
from pydantic.utils import lenient_issubclass
from pydantic.schema import get_flat_models_from_model
from mp_api import __version__
from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel


""" Describes the Materials API Response """


DataT = TypeVar("DataT")


class Meta(BaseModel):

    """
    Meta information for the MAPI Response
    """

    api_version: str = Field(
        __version__,
        description="a string containing the version of the Materials API "
        "implementation, e.g. v0.9.5",
    )

    time_stamp: datetime = Field(
        None,
        description="a string containing the date and time at which the query was executed",
    )

    @validator("time_stamp", pre=True, always=True)
    def default_timestamp(cls, v):
        return v or datetime.utcnow()

    class Config:
        extra = "allow"


class Error(BaseModel):
    """
    Base Error model for Materials API
    """

    code: int = Field(..., description="The error code")
    message: str = Field(..., description="The description of the error")

    @classmethod
    def from_traceback(cls, traceback):
        pass


class Response(GenericModel, Generic[DataT]):
    """
    A Materials API Response
    """

    data: Optional[List[DataT]] = Field(None, description="List of returned data")
    errors: Optional[List[Error]] = Field(
        None, description="Any errors on processing this query"
    )
    meta: Optional[Meta] = Field(None, description="Extra information for the query")

    @validator("errors", always=True)
    def check_consistency(cls, v, values):
        if v is not None and values["data"] is not None:
            raise ValueError("must not provide both data and error")
        if v is None and values.get("data") is None:
            raise ValueError("must provide data or error")
        return v

    @validator("meta", pre=True, always=True)
    def default_meta(cls, v, values):
        if v is None:
            v = Meta().dict()
        else:
            if "total" not in v and values.get("data", None) is not None:
                v["total"] = len(values["data"])
        return v


def api_sanitize(
    pydantic_model: BaseModel,
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
        for name, field in model.__fields__.items():
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
