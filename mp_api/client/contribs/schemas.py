"""Define data models used when querying the client."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal, Self, get_args

import pandas as pd
from pydantic import BaseModel, Field, create_model, field_serializer, field_validator
from pymatgen.core import Structure

from mp_api.client.contribs.utils import flatten_dict, unflatten_dict
from mp_api.client.core.schemas import _DictLikeAccess

CONTRIBS_DOC_NAME = "ContribsDoc"
"""Parent name of the dynamically-created contribs docs, similar to `MPDataDoc`."""


def _cast_pandas_dtype(dtype: type, assume_nullable: bool = True) -> type:
    """Convert pandas dtype to built-in types.

    Args:
        dtype (type) : pandas dtype to convert to builtin (ex., pd.Float64)
        assume_nullable (bool) : whether to assume that a cast type can be nullable.

    Returns:
        type

    Adapted from mpcontribs-lux.
    """
    vname: str = getattr(dtype, "name", str(dtype)).lower()
    inferred_type: type = str
    if "float" in vname:
        inferred_type = float
    elif "int" in vname:
        inferred_type = int
    elif "bool" in vname:
        inferred_type = bool
    return inferred_type | None if assume_nullable else inferred_type


def _get_unit(v: str) -> tuple[str, str | None]:
    """Parse a physical variable name and its optional unit from a string value.

    Ex:
        _get_unit("Temperature [K]") or _get_unit("Temperature (K)")
        will both return "Temperature", "K"

    Args:
        v (str) : input column name to parse

    Returns:
        str : the base name of the physical quantity
        str or None: its optional unit
    """
    if (matched := re.search(r"\(([^)]+)\)|\[([^\]]+)\]", v)) is not None:
        try:
            unit_group = next(
                i for i, x in enumerate(matched.groups()) if x is not None
            )
            unit = matched.groups()[unit_group]
            splitter = f"({unit})" if unit_group == 0 else f"[{unit}]"
            return v.split(splitter, 1)[0].strip(), unit
        except StopIteration:
            pass
    return v, None


def _to_camel_case(v: str) -> str:
    """Convert a generic string to CamelCase.

    Args:
        v (str) : input string

    Returns:
        str : CamelCase string
    """
    split_strs = [y for x in v.lower().split() for y in x.split("_")]
    return "".join(s[0].upper() + s[1:] for s in split_strs)


def _get_pydantic_from_dataframe(
    df: pd.DataFrame,
) -> tuple[type[BaseModel], dict[str, str]]:
    """Dynamically create a pydantic BaseModel from a pandas DataFrame.

    Args:
        df : pandas DataFrame to parse

    Returns:
        BaseModel: the inferred schema of the pandas DataFrame
        dict of str to str: the remapped column names in an
            MP Contribs compatible format.
    """
    columns_renamed = {}
    columns_to_unit = {}
    for col in df.columns:
        base_name, unit = _get_unit(col)
        base_name = _to_camel_case(base_name)
        columns_renamed[col] = base_name
        if unit:
            columns_to_unit[col] = unit

    for col in (c for c, v in columns_to_unit.items() if v is None):
        _ = columns_to_unit.pop(col)

    model_fields = {
        columns_renamed[col_name]: (
            _cast_pandas_dtype(
                df.dtypes[col_name],
                assume_nullable=any(pd.isna(df[col_name])),
            ),
            Field(default=None, description=columns_to_unit.get(col_name)),
        )
        for col_name in df.columns
        if not all(pd.isna(df[col_name]))
    }

    return create_model("InferredModel", **model_fields), columns_renamed


class Reference(_DictLikeAccess):
    """Define schema of URL reference."""

    label: str
    url: str


class Column(_DictLikeAccess):
    """Define schema of MP Contribs column statistics."""

    path: str
    min: float | None = float("nan")
    max: float | None = float("nan")
    unit: str = "NaN"


class Stats(_DictLikeAccess):
    """Define aggregated project statistics schema."""

    columns: int = 0
    contributions: int = 0
    tables: int = 0
    structures: int = 0
    attachments: int = 0
    size: float = 0.0


class ContribsProject(_DictLikeAccess):
    """Define schema for MP Contribs Project."""

    name: str | None = None
    title: str | None = None
    authors: str | None = None
    description: str | None = None
    references: list[Reference] | None = None
    stats: Stats = Field(default_factory=Stats)

    columns: list[Column] = []
    long_title: str | None = None
    is_public: bool = False
    is_approved: bool = False
    unique_identifiers: bool = True
    license: Literal["CCA4", "CCPD"] = "CCA4"
    owner: str | None = None
    other: dict[str, Any] | None = None

    @field_validator("other", mode="before")
    def flatten_other(cls, d: dict) -> dict[str, str | None]:
        """Flatten column metadata."""
        if all(isinstance(v, str) for v in d.values()):
            return d
        return flatten_dict(d)

    @field_serializer("other", mode="plain")
    def unflatten_other(self, v: dict[str, str]) -> dict[str, Any]:
        """Unflatten column metadata."""
        return unflatten_dict(v)


class ContribMeta(_DictLikeAccess):
    """Store metadata about a contributed structure, table, or attachment."""

    id: str
    name: str
    md5: str
    mime: str | None = None


class Datum(_DictLikeAccess):
    """Define schema for numeric contribution data."""

    value: int | float
    error: int | float | None = None
    unit: str = ""

    @property
    def display_name(self) -> str:
        """Format for display."""
        return (
            f"{self.value}"
            + (f" ± {self.error}" if self.error is not None else "")
            + (f" {self.unit}" if self.unit else "")
        )

    def __str__(self) -> str:
        """Format for display."""
        return self.display_name

    def __repr__(self) -> str:
        """Format for display."""
        return self.display_name


class BaseContrib(_DictLikeAccess):
    """Define base schema for a single contribution."""

    id: str | None = None
    project: str | None = None
    formula: str | None = None
    identifier: str | None = None
    is_public: bool = False
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    needs_build: bool = True
    data: dict[str, str | Datum | None] = {}

    @field_validator("data", mode="before")
    def construct_data(cls, d: dict) -> dict[str, str | Datum]:
        if all(isinstance(v, str | Datum) for v in d.values()):
            return d
        flattened_data_dct = flatten_dict(d)
        unique_keys = {
            (
                k.rsplit(".", 1)[0]
                if k.rsplit(".", 1)[-1] in {"value", "error", "unit", "display"}
                else k
            )
            for k in flattened_data_dct
        }
        return {
            k: (
                Datum(
                    **{
                        sub_k: flattened_data_dct.get(f"{k}.{sub_k}", field.default)
                        for sub_k, field in Datum.model_fields.items()
                    }
                )
                if f"{k}.value" in flattened_data_dct
                else flattened_data_dct.get(k)
            )
            for k in unique_keys
        }

    @field_serializer("data", mode="plain")
    def unflatten_data(self, x: dict[str, str | Datum]) -> dict[str, Any]:
        return unflatten_dict(
            {
                k: v.model_dump() if hasattr(v, "model_dump") else v
                for k, v in x.items()
            },
        )


class ContribData(BaseContrib):
    """Schema for data returned by mongo."""

    structures: list[ContribMeta] = []
    tables: list[ContribMeta] = []
    attachments: list[ContribMeta] = []


class ContribSubmission(BaseContrib):
    """Schema for user-submitted contributions.

    NB: We forbid submission of new attachments.
    """

    structures: list[Structure] | None = None
    tables: list[Any] | None = None

    @classmethod
    def from_dataframe(
        cls, df: pd.DataFrame, project: str = "PLACEHOLDER", **kwargs
    ) -> list[Self]:
        """Construct a contribution from a DataFrame."""
        base_model, columns_renamed = _get_pydantic_from_dataframe(df)

        non_null_typs = {
            k: next(t for t in get_args(field.annotation) if t is not None)
            for k, field in base_model.model_fields.items()
        }

        # sanitize data
        sanitized = [
            base_model(
                **{
                    columns_renamed[k]: (
                        non_null_typs[columns_renamed[k]](v) if not pd.isna(v) else None
                    )
                    for k, v in row.to_dict().items()
                }
            ).model_dump()
            for _, row in df.iterrows()
        ]

        non_num_fields = {
            k for k, typ in non_null_typs.items() if typ not in (int, float)
        }

        return [
            cls(
                identifier=str(idx),
                project=project,
                data={
                    k: (
                        entry.get(k)
                        if (k in non_num_fields or entry.get(k) is None)
                        else Datum(value=entry.get(k), unit=field.description or "")  # type: ignore[arg-type]
                    )
                    for k, field in base_model.model_fields.items()
                },
            )
            for idx, entry in enumerate(sanitized)
        ]


class QueryResult(_DictLikeAccess):
    """Result of query_contributions."""

    total_count: int
    total_pages: int
    data: list[BaseModel] | None = None
    has_more: bool = False
