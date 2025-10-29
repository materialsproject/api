from __future__ import annotations

import re
from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING, Literal

import orjson
import pyarrow.dataset as ds
from deltalake import DeltaTable
from emmet.core import __version__ as _EMMET_CORE_VER
from monty.json import MontyDecoder
from packaging.version import parse as parse_version
from pydantic._internal._model_construction import ModelMetaclass

from mp_api.client.core.settings import MAPIClientSettings

if TYPE_CHECKING:
    from monty.json import MSONable


def _compare_emmet_ver(
    ref_version: str, op: Literal["==", ">", ">=", "<", "<="]
) -> bool:
    """Compare the current emmet-core version to a reference for version guarding.

    Example:
        _compare_emmet_ver("0.84.0rc0","<") returns
        emmet.core.__version__ < "0.84.0rc0"

    Parameters
    -----------
    ref_version : str
        A reference version of emmet-core
    op : A mathematical operator
    """
    op_to_op = {"==": "eq", ">": "gt", ">=": "ge", "<": "lt", "<=": "le"}
    return getattr(
        parse_version(_EMMET_CORE_VER),
        f"__{op_to_op.get(op,op)}__",
    )(parse_version(ref_version))


if _compare_emmet_ver("0.85.0", ">="):
    from emmet.core.mpid_ext import validate_identifier
else:
    validate_identifier = None


def load_json(json_like: str | bytes, deser: bool = False, encoding: str = "utf-8"):
    """Utility to load json in consistent manner."""
    data = orjson.loads(
        json_like if isinstance(json_like, bytes) else json_like.encode(encoding)
    )
    return MontyDecoder().process_decoded(data) if deser else data


def _legacy_id_validation(id_list: list[str]) -> list[str]:
    """Legacy utility to validate IDs, pre-AlphaID transition.

    This function is temporarily maintained to allow for
    backwards compatibility with older versions of emmet, and will
    not be preserved.
    """
    pattern = "(mp|mvc|mol|mpcule)-.*"
    if malformed_ids := {
        entry for entry in id_list if re.match(pattern, entry) is None
    }:
        raise ValueError(
            f"{'Entry' if len(malformed_ids) == 1 else 'Entries'}"
            f" {', '.join(malformed_ids)}"
            f"{'is' if len(malformed_ids) == 1 else 'are'} not formatted correctly!"
        )

    return id_list


def validate_ids(id_list: list[str]):
    """Function to validate material and task IDs.

    Args:
        id_list (List[str]): List of material or task IDs.

    Raises:
        ValueError: If at least one ID is not formatted correctly.

    Returns:
        id_list: Returns original ID list if everything is formatted correctly.
    """
    if len(id_list) > MAPIClientSettings().MAX_LIST_LENGTH:
        raise ValueError(
            "List of material/molecule IDs provided is too long. Consider removing the ID filter to automatically pull"
            " data for all IDs and filter locally."
        )

    # TODO: after the transition to AlphaID in the document models,
    # The following line should be changed to
    # return [validate_identifier(idx,serialize=True) for idx in id_list]
    if validate_identifier:
        return [str(validate_identifier(idx)) for idx in id_list]
    return _legacy_id_validation(id_list)


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


class MPDataset:
    def __init__(self, path, document_model, use_document_model):
        """Convenience wrapper for pyarrow datasets stored on disk."""
        self._start = 0
        self._path = path
        self._document_model = document_model
        self._dataset = ds.dataset(path)
        self._row_groups = list(
            chain.from_iterable(
                [
                    fragment.split_by_row_group()
                    for fragment in self._dataset.get_fragments()
                ]
            )
        )
        self._use_document_model = use_document_model

    @property
    def pyarrow_dataset(self) -> ds.Dataset:
        return self._dataset

    @property
    def pydantic_model(self) -> ModelMetaclass:
        return self._document_model

    @property
    def use_document_model(self) -> bool:
        return self._use_document_model

    @use_document_model.setter
    def use_document_model(self, value: bool):
        self._use_document_model = value

    @cached_property
    def delta_table(self) -> DeltaTable:
        return DeltaTable(self._path)

    @cached_property
    def num_chunks(self) -> int:
        return len(self._row_groups)

    def __getitem__(self, idx):
        return list(
            map(
                lambda x: self._document_model(**x) if self._use_document_model else x,
                self._row_groups[idx].to_table().to_pylist(maps_as_pydicts="strict"),
            )
        )

    def __len__(self) -> int:
        return self.num_chunks

    def __iter__(self):
        current = self._start
        while current < self.num_chunks:
            yield self[current]
            current += 1
