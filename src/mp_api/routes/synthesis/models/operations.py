from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Value(BaseModel):
    min_value: float = Field(
        None,
        description="Minimal value."
    )
    max_value: float = Field(
        None,
        description="Maximal value."
    )
    values: List[float] = Field(
        [],
        description="Enumerated values in the literature."
    )
    units: str = Field(
        ...,
        description="Unit of this value."
    )


class Conditions(BaseModel):
    heating_temperature: Optional[List[Value]] = Field(
        None,
        description="Heating temperatures."
    )
    heating_time: Optional[List[Value]] = Field(
        None,
        description="Heating times."
    )
    heating_atmosphere: Optional[List[str]] = Field(
        None,
        description="List of heating atmospheres."
    )
    mixing_device: Optional[str] = Field(
        None,
        description="Mixing device, if this operation is MIXING."
    )
    mixing_media: Optional[str] = Field(
        None,
        description="Mixing media, if this operation is MIXING."
    )


class OperationTypeEnum(str, Enum):
    starting = "StartingSynthesis"
    mixing = "MixingOperation"
    shaping = "ShapingOperation"
    drying = "DryingOperation"
    heating = "HeatingOperation"
    quenching = "QuenchingOperation"


class Operation(BaseModel):
    type: OperationTypeEnum = Field(
        ...,
        description="Type of the operation as classified by the pipeline."
    )
    token: str = Field(
        ...,
        description="Token (word) of the operation as written in paper."
    )
    conditions: Conditions = Field(
        ...,
        description="The conditions linked to this operation."
    )
