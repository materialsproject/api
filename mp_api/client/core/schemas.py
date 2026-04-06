"""Dynamically construct models to use in validating data."""

from __future__ import annotations

from importlib import import_module
from itertools import chain
from typing import TYPE_CHECKING, ForwardRef, Optional, get_args

from emmet.core.utils import jsanitize
from pydantic import BaseModel, create_model

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from pydantic.fields import FieldInfo


class _DictLikeAccess(BaseModel):
    """Define a pydantic mix-in which permits dict-like access to model fields."""

    def __getitem__(self, item: str) -> Any:
        """Return `item` if a valid model field, otherwise raise an exception."""
        if item in self.__class__.model_fields:
            return getattr(self, item)
        raise AttributeError(f"{self.__class__.__name__} has no model field `{item}`.")

    def get(self, item: str, default: Any = None) -> Any:
        """Return a model field `item`, or `default` if it doesn't exist."""
        try:
            return self.__getitem__(item)
        except AttributeError:
            return default

    def __str__(self) -> str:
        """Convenient representation for class for debugging."""
        populated_fields = sorted(
            k for k in self.__class__.model_fields if getattr(self, k, None) is not None
        )
        annos = {k: self.__class__.model_fields[k].annotation for k in populated_fields}
        for k, v in annos.items():
            if hasattr(v, "__name__"):
                annos[k] = v.__name__
        # return f"{self.__class__.__name__}({len(populated_fields)} populated fields)"
        return (
            f"{self.__class__.__name__}(\n"
            + "\n".join(
                f"  {k} ({annos[k]}) : {getattr(self,k)}" for k in populated_fields
            )
            + "\n)"
        )

    def __repr__(self) -> str:
        """Match output of str()."""
        return self.__str__()


def _generate_returned_model(
    doc: dict[str, Any],
    document_model: type[BaseModel],
    model_name: str = "MPDataDoc",
    requested_fields: list[str] | None = None,
) -> tuple[type[BaseModel], set[str], set[str]]:
    """Dynamically generates a pydantic.BaseModel model from API response content.

    Args:
        doc (dict): A single document returned from the API
        document_model (BaseModel) : Document model to infer annotations/validation from
        model_name (str) : Class name of the dynamic model, defaults to "MPDataDoc"
        requested_fields (list of str, or None): Optional list of fields to be returned

    Returns:
        BaseModel: the pydantic model representing the data
        set of str: fields set in the document model
        set of str: set_fields, fields_not_requested)
    """
    model_fields = document_model.model_fields
    set_fields = set(doc).intersection(model_fields)
    unset_fields = set(model_fields).difference(set_fields)
    user_requested_fields: list[str] = requested_fields or []
    fields_not_requested = unset_fields.difference(user_requested_fields)

    # Update with locals() from external module if needed
    if any(
        isinstance(field_meta.annotation, ForwardRef)
        for field_meta in model_fields.values()
    ) or any(
        isinstance(typ, ForwardRef)
        for field_meta in model_fields.values()
        for typ in get_args(field_meta.annotation)
    ):
        vars(import_module(document_model.__module__))

    include_fields: dict[str, tuple[Any, FieldInfo]] = {}
    for name in set_fields:
        field_copy = model_fields[name]._copy()
        if not field_copy.default_factory:
            # Fields with a default_factory cannot also have a default in pydantic>=2.12.3
            field_copy.default = None
        include_fields[name] = (  # type: ignore[assignment]
            Optional[model_fields[name].annotation],
            field_copy,
        )

    data_model = create_model(  # type: ignore
        model_name,
        **include_fields,
        fields_not_requested=(list[str], list(fields_not_requested)),
        unavailable_fields=(
            list[str],
            list(unset_fields.intersection(user_requested_fields)),
        ),
        __base__=_DictLikeAccess,
        __doc__=".".join(
            [getattr(document_model, k, "") for k in ("__module__", "__name__")]
        ),
        __module__=document_model.__module__,
    )

    orig_rester_name = document_model.__name__

    def new_repr(self) -> str:
        extra = ",\n".join(
            f"\033[1m{n}\033[0;0m={getattr(self, n)!r}"
            for n in data_model.model_fields
            if n == "fields_not_requested" or n in set_fields
        )

        s = f"\033[4m\033[1m{self.__class__.__name__}<{orig_rester_name}>\033[0;0m\033[0;0m(\n{extra}\n)"  # noqa: E501
        return s

    def new_str(self) -> str:
        extra = ",\n".join(
            f"\033[1m{n}\033[0;0m={getattr(self, n)!r}"
            for n in data_model.model_fields
            if n in set_fields
        )

        return (
            f"\033[4m\033[1m{self.__class__.__name__}"
            f"<{orig_rester_name}>\033[0;0m\033[0;0m"
            f"\n{extra}\n\n"
            f"\033[1mFields not requested:\033[0;0m\n{fields_not_requested}"
        )

    def new_getattr(self, attr) -> str:
        if attr in self.unavailable_fields:
            raise AttributeError(f"`{attr}` is unavailable in the returned data.")
        if attr in self.fields_not_requested:
            raise AttributeError(
                f"`{attr}` data is available but has not been requested in `fields`."
                " A full list of unrequested fields can be found in `fields_not_requested`."
            )
        else:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {attr!r}"
            )

    def new_dict(self, *args, **kwargs):
        d = super(data_model, self).model_dump(*args, **kwargs)
        return jsanitize(d)

    data_model.__repr__ = new_repr
    data_model.__str__ = new_str
    data_model.__getattr__ = new_getattr
    data_model.dict = new_dict

    return data_model, set_fields, fields_not_requested


def _convert_to_model(
    data: list[dict[str, Any]] | Iterator,
    document_model: type[BaseModel],
    model_name: str = "MPDataDoc",
    requested_fields: list[str] | None = None,
) -> list[BaseModel] | list[dict[str, Any]]:
    """Converts dictionary documents to dynamically instantiated pydantic objects.

    Args:
        data (list[dict] or Iterator): Raw dictionary data objects
        document_model (BaseModel) : Document model to infer annotations/validation from
        model_name (str) : Class name of the dynamic model, defaults to "MPDataDoc"
        requested_fields (list[str] or None): Optional list of fields to be returned

    Returns:
        (list[BaseModel]): List of pydantic.BaseModel objects

    """
    if (hasattr(data, "__len__") and len(data) > 0) or (hasattr(data, "__next__")):  # type: ignore[arg-type]
        is_list = hasattr(data, "__len__")
        try:
            # Handle both list-like and iterator input
            first_doc = data[0] if is_list else next(data)  # type: ignore[index,arg-type]
        except StopIteration:
            # Return empty list if no data in iterator
            return []
        data_model, set_fields, _ = _generate_returned_model(
            first_doc, document_model, model_name, requested_fields=requested_fields
        )

        return [
            data_model(
                **{field: raw_doc[field] for field in set_fields.intersection(raw_doc)}
            )
            for raw_doc in (data if is_list else chain([first_doc], data))
        ]

    return data
