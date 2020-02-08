from datetime import datetime
from pymatgen import Element
from mp_api import __version__
from pydantic import BaseModel, Field, validator
from typing import Optional, List

""" Describes the Materials API Response """


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

    total: Optional[int] = Field(
        None, description="the total number of documents available for this query", ge=0
    )

    elements: Optional[List[Element]] = Field(
        None, description="The list of elements covered by this query"
    )

    @validator("time_stamp", pre=True, always=True)
    def default_timestamp(cls, v):
        return v or datetime.utcnow()


class Error(BaseModel):
    """
    Base Error model for Materials API
    """

    code: int = Field(..., description="The error code")
    message: str = Field(..., description="The description of the error")

    @classmethod
    def from_traceback(cls, tracebac):
        pass


class Response(BaseModel):
    """
    A Materials API Response
    """

    data: Optional[List] = Field(None, description="List of returned data")
    errors: Optional[List[Error]] = Field(
        None, description="Any errors on processing this query"
    )
    meta: Meta = Field(None, description="Extra information for the query")

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
            v = Meta()
        else:
            if "total" not in v and values.get("data", None) is not None:
                v["total"] = len(values["data"])
        return v
