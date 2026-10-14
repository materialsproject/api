from __future__ import annotations

import os
import warnings
from functools import cached_property
from importlib import import_module
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote, urljoin

import orjson
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from deltalake import DeltaTable
from emmet.core import __version__ as _EMMET_CORE_VER
from emmet.core.mpid import validate_identifier
from monty.json import MontyDecoder
from packaging.version import parse as parse_version

from mp_api.client.core._display import mp_advice, mp_warning
from mp_api.client.core._external import track_calls
from mp_api.client.core.exceptions import (
    MPDatasetIndexingWarning,
    MPDatasetIterationWarning,
    MPDatasetSlicingWarning,
    MPRestError,
)
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any, Literal

    from pydantic._internal._model_construction import ModelMetaclass


def _compare_emmet_ver(
    ref_version: str, op: Literal["==", ">", ">=", "<", "<="]
) -> bool:
    """Compare the current emmet-core version to a reference for version guarding.

    Example:
        _compare_emmet_ver("0.84.0rc0","<") returns
        emmet.core.__version__ < "0.84.0rc0"

    This function may not be used anywhere in the client, but it should
    be preserved for future use, in case some degree of backwards
    compatibility or feature buy-in is needed.

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


def to_partition_version(db_version: str) -> str:
    """Convert a database version to the form used for DeltaTable partitions.

    Partition values use dashes where the database version uses dots,
    e.g. "2026.04.13" -> "2026-04-13" and "2026.04.13.post1" -> "2026-04-13-post1".
    Dashes and underscores are accepted in the input too.

    Args:
        db_version (str) : database version, e.g. "2026.04.13"

    Returns:
        str : partition value, e.g. "2026-04-13"
    """
    return db_version.strip().lstrip("v").replace(".", "-").replace("_", "-")


def to_db_version(partition_version: str) -> str:
    """Convert a DeltaTable partition value to the database version form.

    The inverse of `to_partition_version`, e.g. "2026-04-13" -> "2026.04.13".

    Args:
        partition_version (str) : partition value, e.g. "2026-04-13"

    Returns:
        str : database version, e.g. "2026.04.13"
    """
    return to_partition_version(partition_version).replace("-", ".")


def load_json(
    json_like: str | bytes, deser: bool = False, encoding: str = "utf-8"
) -> Any:
    """Utility to load json in consistent manner."""
    data = orjson.loads(
        json_like if isinstance(json_like, bytes) else json_like.encode(encoding)
    )
    return MontyDecoder().process_decoded(data) if deser else data


def validate_api_key(api_key: str | None = None) -> str | None:
    """Find and validate an API key."""
    # SETTINGS tries to read API key from ~/.config/.pmgrc.yaml
    api_key = api_key or os.getenv("MP_API_KEY")
    if not api_key:
        from pymatgen.core import SETTINGS as PMG_SETTINGS

        api_key = PMG_SETTINGS.get("PMG_MAPI_KEY")

    if not api_key:
        # The web server requires the client to initialize without an API key.
        # Only warn the user if the API key cannot be identified to permit
        # the web server to run.
        mp_warning(
            "No API key found, please set explicitly or in "
            "the `MP_API_KEY` environment variable.",
            stacklevel=2,
        )

    elif isinstance(api_key, str) and len(api_key) != 32:
        raise MPRestError(
            "Please obtain a valid API key from https://materialsproject.org/api "
            "and export it as an environment variable `MP_API_KEY`. "
            "Valid API keys are 32 characters."
        )

    return api_key


LEGACY_ID_PREFIXES: frozenset[str] = frozenset({"mvc"})
"""Prefixes of identifiers that used to exist in the database but were removed."""


def _shortlist(items: list[Any], sep: str = ", ", limit: int = 10) -> str:
    """The first `limit` items joined by `sep`, noting how many were left out."""
    shown = sep.join(map(str, items[:limit]))
    if len(items) > limit:
        shown += f"{sep}... ({len(items) - limit:,} more)"
    return shown


def _is_legacy_id(idx: Any) -> bool:
    return isinstance(idx, str) and idx.split("-", 1)[0] in LEGACY_ID_PREFIXES


def validate_ids(id_list: Iterable[Any], *, user_input: bool = True) -> list[str]:
    """Validate and format Materials Project identifiers (material and task IDs).

    Identifiers are checked strictly (see `emmet.core.mpid.validate_identifier`
    with `strict=True`): a bare ID ("149", "aaaaaaft") or "<prefix>-<id>" with
    a known prefix ("mp-149"). Invalid identifiers are dropped and reported
    together in one `MPRestWarning`, which the caller can act on. Legacy
    identifiers (e.g. "mvc-149"), which were removed from the database, are
    dropped with a notice of their own.

    Args:
        id_list (Iterable) : identifiers given by the user, or returned by the API
        user_input (bool) : True for identifiers the user passed. False for
            identifiers the API returned, for which an invalid one is a bug, so
            an `MPRestError` is raised instead of a warning.

    Raises:
        MPRestError: if too many identifiers are given, if none is valid, or
            (with `user_input=False`) if any is invalid.

    Returns:
        list of str : the valid identifiers, formatted, in their input order
    """
    from mp_api.client.core._external import user_stacklevel

    id_list = list(id_list)
    if len(id_list) > MAPI_CLIENT_SETTINGS.MAX_LIST_LENGTH:
        raise MPRestError(
            "List of material/molecule IDs provided is too long. Consider removing the ID filter to automatically pull"
            " data for all IDs and filter locally."
        )

    valid: list[str] = []
    legacy: list[str] = []
    invalid: list[str] = []
    for idx in id_list:
        if _is_legacy_id(idx):
            legacy.append(idx)
            continue
        try:
            parsed = validate_identifier(idx, serialize=False, strict=True)
        except ValueError as exc:
            invalid.append(str(exc))
            continue
        valid.append(getattr(parsed, "string", str(parsed)))

    if not user_input and (invalid or legacy):
        raise MPRestError(
            "The Materials Project API returned invalid identifiers: "
            + _shortlist(invalid + [repr(idx) for idx in legacy], sep="; ")
        )

    stacklevel = user_stacklevel()
    if legacy:
        mp_warning(
            "These IDs refer to legacy calculations that have been removed from the "
            f"Materials Project database, and are ignored: {_shortlist(legacy)}",
            stacklevel=stacklevel,
        )
    if invalid:
        reasons = [f"{reason.rstrip('.')}." for reason in invalid]
        mp_warning(
            "Ignoring invalid IDs. Materials Project IDs are a bare ID, e.g. "
            "'149' or 'aaaaaaft', or '<prefix>-<id>', e.g. 'mp-149'. "
            + _shortlist(reasons, sep=" "),
            stacklevel=stacklevel,
        )
    if id_list and not valid:
        raise MPRestError(f"No valid IDs to query (ignored: {_shortlist(id_list)}).")
    return valid


def validate_endpoint(endpoint: str | None, suffix: str | None = None) -> str:
    """Validate an endpoint with optional suffix.

    NB: does not modify the endpoint in place,
    returns a new variable.

    Parameters
    -----------
    endpoint : str or None (default)
        A string representing the endpoint URL or the default
        in `mp_api.client.core.settings`
    suffix : str or None (default)
        Optional suffix to append to the endpoint.

    Returns:
    -----------
    str : the validated endpoint
    """
    new_endpoint = endpoint or MAPI_CLIENT_SETTINGS.ENDPOINT
    if suffix:
        new_endpoint = urljoin(new_endpoint, suffix)
    if not new_endpoint.endswith("/"):
        new_endpoint += "/"
    return new_endpoint


class LazyImport:
    """Lazily import and load an object.

    This class is super lazy, in that it lazily imports and caches an object.
    If the object is a function, the function itself will be cached.

    If the object is a class, and the class is initialized, the
    current instance of the class will be cached.

    Parameters
    -----------
    import_str : str
        A dot-separated, import-like string.
    """

    __slots__ = ["_module_name", "_class_name", "_obj", "_imported"]

    def __init__(
        self,
        import_str: str,
    ) -> None:
        """Initialize a lazily imported object.

        Parameters
        -----------
        import_str : str
            A dot-separated, import-like string.
        """
        if len(split_import_str := import_str.rsplit(".", 1)) == 1:
            self._module_name: str = split_import_str[0]
            self._class_name: str | None = None
        else:
            self._module_name, self._class_name = split_import_str

        self._imported: Any | None = None
        self._obj: Any | None = None

    def copy(self) -> LazyImport:
        """Return a new copy of the current instance."""
        return LazyImport(
            f"{self._module_name}"
            + (f".{self._class_name}" if self._class_name else "")
        )

    def __str__(self) -> str:
        return f"LazyImport of {self._module_name}" + (
            f".{self._class_name}" if self._class_name else ""
        )

    def __repr__(self) -> str:
        return self.__str__()

    def _load(
        self,
    ) -> None:
        try:
            _imported = import_module(self._module_name)
            if self._class_name:
                _imported = getattr(_imported, self._class_name)
            self._imported = _imported
        except Exception as exc:
            raise ImportError(
                f"Failed to import {self._module_name}.{self._class_name}:\n{exc}"
            )

    def __call__(self, *args, **kwargs) -> Any:
        """Call a function or (re-)initialize a class.

        If the object itself has not been imported, this will first import it.

        If the object is a class, it will be initialized, cached, and returned.

        If the object is a function, it will be cached, and this will return
        the value(s) of the function at (*args,**kwargs).
        """
        if self._imported is None:
            self._load()

        if isinstance(self._imported, type):
            self._obj = self._imported(*args, **kwargs)
            return self._obj
        elif callable(self._imported):
            self._obj = self._imported
            return self._obj(*args, **kwargs)  # type: ignore[misc]

    def __getattr__(self, v: str) -> Any:
        """Get an attribute on a super lazy object."""
        if self._obj is not None and hasattr(self._obj, v):
            return getattr(self._obj, v)

        if self._imported is None:
            self._load()
        if hasattr(self._imported, v):
            return getattr(self._imported, v)

        raise AttributeError(
            f"{self._module_name}{'.' + self._class_name if self._class_name else ''} "
            f"has no attribute {v}"
        )

    def __dir__(self) -> Iterable[str]:
        return self._obj.__dir__() if hasattr(self._obj, "__dir__") else []


@track_calls
class MPDataset:
    """Convenience wrapper for pyarrow datasets stored on disk."""

    def __init__(
        self,
        path: str | Path,
        document_model: ModelMetaclass,
        use_document_model: bool,
        version: str | None = None,
    ):
        """Initialize a MPDataset.

        Parameters
        -----------
        path: str | Path
            A path-like string.
        document_model: ModelMetaclass
            Pydantic document model for use during de-serialization of arrow data
        use_document_model: bool
            Use 'document_model' during de-serialization of arrow data.
        version: str | None
            Database version to read, for datasets partitioned by version,
            e.g. "2026.04.13". If None, all data in the dataset is read.
        """
        self._start: int = 0
        self._path = Path(path)
        self._document_model: ModelMetaclass = document_model
        self._version = to_db_version(version) if version else None
        self._dataset = self._open_dataset()
        self._row_groups: list[Any] = list(
            chain.from_iterable(
                [
                    fragment.split_by_row_group()
                    for fragment in self._dataset.get_fragments()
                ]
            )
        )
        self._use_document_model = use_document_model

    def _open_dataset(self) -> ds.Dataset:
        """Open the data files that the DeltaTable's current version uses.

        The file list comes from the Delta log, so files left behind by an
        interrupted download, or removed from the table but not yet vacuumed,
        are not read. Without a Delta log, every file in the directory is read.

        The files are opened directly with pyarrow rather than through
        `DeltaTable.to_pyarrow_dataset()`: reading through deltalake's
        filesystem can hang the interpreter at exit (delta-rs 1.5.1).
        """
        if not DeltaTable.is_deltatable(str(self._path)):
            return ds.dataset(self._path)

        table = DeltaTable(self._path)
        actions = pa.table(table.get_add_actions(flatten=True))
        if self._version and "version" in table.metadata().partition_columns:
            actions = actions.filter(
                pc.equal(  # type: ignore[attr-defined]
                    actions["partition.version"],
                    to_partition_version(self._version),
                )
            )
        # Paths in the log are relative to the table root and URL-encoded
        files = [str(self._path / unquote(rel)) for rel in actions["path"].to_pylist()]
        return ds.dataset(
            files, schema=self._file_schema(table, files), format="parquet"
        )

    @staticmethod
    def _file_schema(table: DeltaTable, files: list[str]) -> pa.Schema | None:
        """Schema of the data files, used when there are none to infer it from.

        Partition columns (e.g. version) are stored in the directory names,
        not the files, so they are left out.
        """
        if files:
            return None
        partition_columns = set(table.metadata().partition_columns)
        schema = pa.schema(table.schema().to_arrow())  # type: ignore[arg-type]
        return pa.schema([f for f in schema if f.name not in partition_columns])

    @property
    def version(self) -> str | None:
        """The database version this dataset reads, e.g. "2026.04.13"."""
        return self._version

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
        if isinstance(idx, slice):
            mp_advice(
                "Pythonic slicing of arrow-based MPDatasets is sub-optimal, consider "
                "using idiomatic arrow patterns. See MP's docs on MPDatasets for "
                "relevant examples: "
                "docs.materialsproject.org/materials-project-data-lakehouse/arrow-datasets",
                MPDatasetSlicingWarning,
                stacklevel=2,
            )
            start, stop, step = idx.indices(len(self))
            _take = list(range(start, stop, step))
            ds_slice = self._dataset.take(_take).to_pylist(maps_as_pydicts="strict")
            return (
                [self._document_model(**_row) for _row in ds_slice]
                if self._use_document_model
                else ds_slice
            )

        mp_advice(
            "Pythonic indexing into arrow-based MPDatasets is sub-optimal, consider "
            "using idiomatic arrow patterns. See MP's docs on MPDatasets for "
            "relevant examples: "
            "docs.materialsproject.org/materials-project-data-lakehouse/arrow-datasets",
            MPDatasetIndexingWarning,
            stacklevel=2,
        )
        _row = self._dataset.take([idx]).to_pylist(maps_as_pydicts="strict")[0]
        return self._document_model(**_row) if self._use_document_model else _row

    def __len__(self) -> int:
        return self._dataset.count_rows()

    def __iter__(self):
        with warnings.catch_warnings(
            action="ignore", category=MPDatasetIndexingWarning
        ):
            mp_advice(
                "Iterating through arrow-based MPDatasets is sub-optimal, consider "
                "using idiomatic arrow patterns. See MP's docs on MPDatasets for "
                "relevant examples: "
                "docs.materialsproject.org/materials-project-data-lakehouse/arrow-datasets",
                MPDatasetIterationWarning,
                stacklevel=2,
            )
            current = self._start
            while current < len(self):
                yield self[current]
                current += 1
