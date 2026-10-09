"""This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

from __future__ import annotations

import gzip
import inspect
import itertools
import json
import logging
import os
import platform
import shutil
import sys
import time
import uuid
import warnings
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import ExitStack
from copy import copy
from functools import cache
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from itertools import batched, chain
from json import JSONDecodeError
from math import ceil
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote, urljoin

import boto3
import pyarrow as pa
import pyarrow.dataset as ds
import requests
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
from deltalake import DeltaTable, QueryBuilder, Schema
from deltalake.transaction import AddAction, create_table_with_add_actions
from emmet.core.arrow import arrowize
from emmet.core.utils import jsanitize
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from mp_api.client._server_utils import get_consumer, get_user_api_key, is_dev_env
from mp_api.client.core._display import ProgressHandle, mp_warning, progress_bar, status
from mp_api.client.core.delta import DeltaCatalog
from mp_api.client.core.exceptions import (
    MPRestError,
    _emit_status_warning,
)
from mp_api.client.core.schemas import _convert_to_model, _DictLikeAccess
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS
from mp_api.client.core.utils import (
    MPDataset,
    load_json,
    to_db_version,
    to_partition_version,
    validate_endpoint,
    validate_ids,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Any

    from arro3.core import RecordBatchReader

    from mp_api.client.core.utils import LazyImport

try:
    __version__ = version("mp_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION", "")

STATIC_COLLECTIONS = [
    "eos",
    "grain-boundaries",
    "jcesr",
    "molecules",
    "phonon",
    "snls",
    "surface-properties",
    "synth-descriptions",
    "xas",
]
# Routes whose S3 dataset name differs from the route name
S3_COLLECTION_NAMES = {
    "molecules/summary": "molecules",
    "molecules/jcesr": "jcesr",
    "materials/synthesis": "synth-descriptions",
}
CONTROLLED_COLLECTIONS = [
    "chemenv",
    "materials",
    "oxidation-states",
    "summary",
    "tasks",
    "thermo",
]

logger = logging.getLogger(__name__)

LATEST_DB_VERSION = "latest"


def _normalize_db_version(db_version: str | None) -> str:
    """Normalize a user-given database version, e.g. "2026-04-13" -> "2026.04.13".

    "latest" (any case) is kept as "latest", and None becomes "".
    """
    if not db_version:
        return ""
    if db_version.strip().lower() == LATEST_DB_VERSION:
        return LATEST_DB_VERSION
    return to_db_version(db_version)


class QueryBuilderWithCache(QueryBuilder):
    def __init__(self, catalog: DeltaCatalog | None = None, _warn: bool = True) -> None:
        """Deprecated: use `mp_api.client.core.delta.DeltaCatalog`.

        Kept for backwards compatibility. Tables registered here, and
        queries run through it, are delegated to a `DeltaCatalog`. Resters
        given this object via `query_builder=` share its catalog.

        Args:
            catalog (DeltaCatalog or None) : catalog to delegate to.
                A new one is created if None.
            _warn (bool) : internal, whether to emit a DeprecationWarning
        """
        if _warn:
            warnings.warn(
                "QueryBuilderWithCache is deprecated and will be removed in a future "
                "release. Pass `delta_catalog=DeltaCatalog()` "
                "(from mp_api.client.core.delta) to MPRester instead.",
                FutureWarning,
                stacklevel=2,
            )
        self.catalog: DeltaCatalog = catalog if catalog is not None else DeltaCatalog()
        super().__init__()

    @property
    def _delta_tables(self) -> dict[str, DeltaTable]:
        """Map of table names (labels) to DeltaTable instances."""
        return self.catalog.tables

    def register(self, table_name: str, delta_table: DeltaTable) -> QueryBuilder:
        """Register a DeltaTable in the underlying catalog."""
        self.catalog.add(table_name, delta_table)
        return self

    def execute(self, sql: str) -> RecordBatchReader:
        """Execute SQL against the tables in the underlying catalog."""
        return self.catalog._execute_raw(sql)


class _Rester:
    """Define base attributes of a REST client."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        include_user_agent: bool = True,
        use_document_model: bool = True,
        session: requests.Session | None = None,
        headers: dict | None = None,
        mute_progress_bars: bool = MAPI_CLIENT_SETTINGS.MUTE_PROGRESS_BARS,
        db_version: str | None = None,
        local_dataset_cache: (
            str | os.PathLike
        ) = MAPI_CLIENT_SETTINGS.LOCAL_DATASET_CACHE,
        force_renew: bool = False,
        query_builder: QueryBuilderWithCache | None = None,
        delta_catalog: DeltaCatalog | None = None,
        **kwargs,
    ) -> None:
        """Initialize a RESTer.

        Arguments:
            api_key: A String API key for accessing the MaterialsProject
                REST interface. Please obtain your API key at
                https://www.materialsproject.org/dashboard. If this is None,
                the code will check if there is a "PMG_MAPI_KEY" setting.
                If so, it will use that environment variable. This makes
                easier for heavy users to simply add this environment variable to
                their setups and MPRester can then be called without any arguments.
            endpoint: Url of endpoint to access the MaterialsProject REST
                interface. Defaults to the standard Materials Project REST
                address at "https://api.materialsproject.org", but
                can be changed to other urls implementing a similar interface.
            include_user_agent: If True, will include a user agent with the
                HTTP request including information on pymatgen and system version
                making the API request. This helps MP support pymatgen users, and
                is similar to what most web browsers send with each page request.
                Set to False to disable the user agent.
            use_document_model: If False, skip the creating the document model and return data
                as a dictionary. This can be simpler to work with but bypasses data validation
                and will not give auto-complete for available fields.
            session: requests Session object with which to connect to the API, for
                advanced usage only.
            headers: Custom headers for localhost connections.
            mute_progress_bars: Whether to disable progress bars.
            db_version (str) : Database version to use for data read from S3 (full dataset
                downloads, phase diagrams), e.g. "2026.04.13". Defaults to the version
                currently served by the API. REST queries always use the current database.
                See `available_db_versions()` on a rester for the versions available.
            local_dataset_cache: Target directory for downloading full datasets. Defaults
                to 'mp_datasets' in the user's home directory
            force_renew: Option to overwrite existing local dataset
            query_builder : DEPRECATED, use `delta_catalog`. Instance of QueryBuilderWithCache
                whose catalog is used for querying delta tables.
                NOTE: Must be a QueryBuilderWithCache, a deltalake.QueryBuilder will be ignored.
            delta_catalog : Instance of DeltaCatalog to use for querying delta tables.
                Share one instance across resters (e.g. one per web-server worker) to
                reuse loaded table snapshots. Takes precedence over `query_builder`.
            **kwargs: access to legacy kwargs that may be in the process of being deprecated
        """
        self.api_key = get_user_api_key(api_key=api_key)
        self.endpoint = validate_endpoint(endpoint)

        self.include_user_agent = include_user_agent
        self.use_document_model = use_document_model

        # Copy, so neither the caller's dict nor (below) a shared session is mutated
        self.headers = dict(headers or get_consumer())
        if is_dev_env() and self.api_key:
            self.headers["x-api-key"] = self.api_key

        self._session = session or _Rester._create_session(
            api_key=self.api_key,
            include_user_agent=self.include_user_agent,
            headers=self.headers,
        )

        self.use_document_model = use_document_model
        self.mute_progress_bars = mute_progress_bars
        self.db_version: str = _normalize_db_version(db_version)
        self.local_dataset_cache = Path(local_dataset_cache)
        self.force_renew = force_renew
        self._query_builder = (
            query_builder if isinstance(query_builder, QueryBuilderWithCache) else None
        )
        if self._query_builder is not None and delta_catalog is None:
            delta_catalog = self._query_builder.catalog
        self._delta_catalog: DeltaCatalog | None = delta_catalog

        if "monty_decode" in kwargs:
            # Pop to not repeatedly trigger warning to the user
            kwargs.pop("monty_decode", None)
            warnings.warn(
                "Ignoring `monty_decode`, as it is no longer a supported option in `mp_api`."
                "The client by default returns results consistent with `monty_decode=True`.",
                FutureWarning,
                stacklevel=2,
            )

    @property
    def session(self) -> requests.Session:
        if not self._session:
            self._session = self._create_session(
                self.api_key, self.include_user_agent, self.headers
            )
        return self._session

    @property
    def _docs_description(self) -> str:
        """E.g. "SummaryDoc documents", for progress bars and messages."""
        name = getattr(getattr(self, "document_model", None), "__name__", "")
        return f"{name} documents" if name and not name.startswith("_") else "documents"

    @property
    def delta_catalog(self) -> DeltaCatalog:
        """The DeltaCatalog used for delta-backed queries, created on first use."""
        if self._delta_catalog is None:
            self._delta_catalog = DeltaCatalog()
        return self._delta_catalog

    @property
    def query_builder(self) -> QueryBuilderWithCache:
        """Deprecated: use `delta_catalog`."""
        warnings.warn(
            "`query_builder` is deprecated, use `delta_catalog` instead.",
            FutureWarning,
            stacklevel=2,
        )
        if self._query_builder is None:
            self._query_builder = QueryBuilderWithCache(
                catalog=self.delta_catalog, _warn=False
            )
        return self._query_builder

    @staticmethod
    def _create_session(api_key, include_user_agent, headers):
        session = requests.Session()
        session.headers = {"x-api-key": api_key}
        session.headers.update(headers)

        if include_user_agent:
            mp_api_info = "mp-api/" + __version__ if __version__ else None
            python_info = f"Python/{sys.version.split()[0]}"
            platform_info = f"{platform.system()}/{platform.release()}"
            user_agent = f"{mp_api_info} ({python_info} {platform_info})"
            session.headers["user-agent"] = user_agent

        max_retry_num = MAPI_CLIENT_SETTINGS.MAX_RETRIES
        retry = Retry(
            total=max_retry_num,
            read=max_retry_num,
            connect=max_retry_num,
            respect_retry_after_header=True,
            status_forcelist=[429, 504, 502],  # rate limiting
            backoff_factor=MAPI_CLIENT_SETTINGS.BACKOFF_FACTOR,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def __enter__(self):  # pragma: no cover
        """Support for "with" context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        """Support for "with" context."""
        if self.session is not None:
            self.session.close()
        self._session = None

    @staticmethod
    @cache
    def _get_heartbeat_info(endpoint) -> tuple[str, list[str]]:
        """DB version:
        The Materials Project database is periodically updated and has a
        database version associated with it. When the database is updated,
        consolidated data (information about "a material") may and does
        change, while calculation data about a specific calculation task
        remains unchanged and available for querying via its task_id.

        The database version is set as a date in the format YYYY_MM_DD,
        where "_DD" may be optional. An additional numerical or `postN` suffix
        might be added if multiple releases happen on the same day.

        Access Controlled Datasets:
        Certain contributions to the Materials Project have access
        control restrictions that require explicit agreement to the
        Terms of Use for the respective datasets prior to access being
        granted.

        A full list of the Terms of Use for all contributions in the
        Materials Project are available at:

        https://next-gen.materialsproject.org/about/terms

        Returns:
            tuple with database version as a string and a comma separated
            string with all calculation batch identifiers that have access
            restrictions
        """
        if (get_resp := requests.get(url=endpoint + "heartbeat")).status_code == 403:
            _emit_status_warning()
            return (
                "",
                [],
            )  # Catiously do not allow access to any access controlled `batch_id`s
        response = get_resp.json()
        return response["db_version"], response["access_controlled_batch_ids"]


class BaseRester(_Rester):
    """Base client class with core stubs."""

    suffix: str = ""
    document_model: type[BaseModel] = _DictLikeAccess
    primary_key: str = "material_id"
    delta_backed: bool = True

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        include_user_agent: bool = True,
        use_document_model: bool = True,
        session: requests.Session | None = None,
        headers: dict | None = None,
        mute_progress_bars: bool = MAPI_CLIENT_SETTINGS.MUTE_PROGRESS_BARS,
        db_version: str | None = None,
        local_dataset_cache: (
            str | os.PathLike
        ) = MAPI_CLIENT_SETTINGS.LOCAL_DATASET_CACHE,
        force_renew: bool = False,
        query_builder: QueryBuilderWithCache | None = None,
        delta_catalog: DeltaCatalog | None = None,
        s3_client: Any | None = None,
        timeout: int = 20,
        **kwargs,
    ):
        """Initialize the REST API helper class.

            s3_client: boto3 S3 client object with which to connect to the object stores.
            timeout: Time in seconds to wait until a request timeout error is thrown

        Arguments:
            api_key: A String API key for accessing the MaterialsProject
                REST interface. Please obtain your API key at
                https://www.materialsproject.org/dashboard. If this is None,
                the code will check if there is a "PMG_MAPI_KEY" setting.
                If so, it will use that environment variable. This makes
                easier for heavy users to simply add this environment variable to
                their setups and MPRester can then be called without any arguments.
            endpoint: Url of endpoint to access the MaterialsProject REST
                interface. Defaults to the standard Materials Project REST
                address at "https://api.materialsproject.org", but
                can be changed to other urls implementing a similar interface.
            include_user_agent: If True, will include a user agent with the
                HTTP request including information on pymatgen and system version
                making the API request. This helps MP support pymatgen users, and
                is similar to what most web browsers send with each page request.
                Set to False to disable the user agent.
            session: requests Session object with which to connect to the API, for
                advanced usage only.
            use_document_model: If False, skip the creating the document model and return data
                as a dictionary. This can be simpler to work with but bypasses data validation
                and will not give auto-complete for available fields.
            headers: Custom headers for localhost connections.
            mute_progress_bars: Whether to disable progress bars.
            db_version (str) : Database version to use for data read from S3 (full dataset
                downloads, phase diagrams), e.g. "2026.04.13". Defaults to the version
                currently served by the API. REST queries always use the current database.
                See `available_db_versions()` on a rester for the versions available.
            local_dataset_cache: Target directory for downloading full datasets. Defaults
                to 'mp_datasets' in the user's home directory
            force_renew: Option to overwrite existing local dataset
            query_builder : DEPRECATED, use `delta_catalog`. Instance of QueryBuilderWithCache
                whose catalog is used for querying delta tables.
                NOTE: Must be a QueryBuilderWithCache, a deltalake.QueryBuilder will be ignored.
            delta_catalog : Instance of DeltaCatalog to use for querying delta tables.
            s3_client: boto3 S3 client object with which to connect to the object stores.
            timeout: Time in seconds to wait until a request timeout error is thrown
            **kwargs: access to legacy kwargs that may be in the process of being deprecated
        """
        super().__init__(
            api_key=api_key,
            endpoint=endpoint,
            include_user_agent=include_user_agent,
            use_document_model=use_document_model,
            session=session,
            headers=headers,
            mute_progress_bars=mute_progress_bars,
            db_version=db_version,
            local_dataset_cache=local_dataset_cache,
            force_renew=force_renew,
            query_builder=query_builder,
            delta_catalog=delta_catalog,
            **kwargs,
        )

        self.base_endpoint = validate_endpoint(endpoint)
        self.endpoint = validate_endpoint(endpoint, suffix=self.suffix)

        (
            hb_db_version,
            self.access_controlled_batch_ids,
        ) = self._get_heartbeat_info(self.base_endpoint)
        # The version the REST API serves, may differ from self.db_version
        self.current_db_version: str = hb_db_version
        if not self.db_version:
            self.db_version = hb_db_version

        self.timeout = timeout
        self._s3_client = s3_client

    @property
    def s3_client(self):
        if not self._s3_client:
            self._s3_client = boto3.client(
                "s3",
                config=Config(signature_version=UNSIGNED),  # type: ignore
            )
        return self._s3_client

    def _post_resource(
        self,
        body: dict | None = None,
        params: dict | None = None,
        suburl: str | None = None,
        use_document_model: bool | None = None,
    ) -> dict:
        """Post data to the endpoint for a Resource.

        Arguments:
            body: body json to send in post request
            params: extra params to send in post request
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """
        if use_document_model is None:
            use_document_model = self.use_document_model

        payload = jsanitize(body)

        try:
            url = validate_endpoint(self.endpoint, suffix=suburl)
            response = self.session.post(url, json=payload, verify=True, params=params)

            if response.status_code == 200:
                data = load_json(response.text)
                if self.document_model and use_document_model:
                    if isinstance(data["data"], dict):
                        data["data"] = self.document_model.model_validate(data["data"])  # type: ignore
                    elif isinstance(data["data"], list):
                        data["data"] = [
                            self.document_model.model_validate(d) for d in data["data"]
                        ]  # type: ignore

                return data

            else:
                try:
                    data = load_json(response.text)["detail"]
                except (JSONDecodeError, KeyError):
                    data = f"Response {response.text}"
                if isinstance(data, str):
                    message = data
                else:
                    try:
                        message = ", ".join(
                            f"{entry['loc'][1]} - {entry['msg']}" for entry in data
                        )
                    except (KeyError, IndexError):
                        message = str(data)

                raise MPRestError(
                    f"REST post query returned with error status code {response.status_code} "
                    f"on URL {response.url} with message:\n{message}"
                )

        except RequestException as ex:
            raise MPRestError(str(ex))

    def _patch_resource(
        self,
        body: dict | None = None,
        params: dict | None = None,
        suburl: str | None = None,
        use_document_model: bool | None = None,
    ) -> dict:
        """Patch data to the endpoint for a Resource.

        Arguments:
            body: body json to send in patch request
            params: extra params to send in patch request
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """
        if use_document_model is None:
            use_document_model = self.use_document_model

        payload = jsanitize(body)

        try:
            url = validate_endpoint(self.endpoint, suffix=suburl)
            response = self.session.patch(url, json=payload, verify=True, params=params)

            if response.status_code == 200:
                data = load_json(response.text)
                if self.document_model and use_document_model:
                    if isinstance(data["data"], dict):
                        data["data"] = self.document_model.model_validate(data["data"])  # type: ignore
                    elif isinstance(data["data"], list):
                        data["data"] = [
                            self.document_model.model_validate(d) for d in data["data"]
                        ]  # type: ignore

                return data

            else:
                try:
                    data = load_json(response.text)["detail"]
                except (JSONDecodeError, KeyError):
                    data = f"Response {response.text}"
                if isinstance(data, str):
                    message = data
                else:
                    try:
                        message = ", ".join(
                            f"{entry['loc'][1]} - {entry['msg']}" for entry in data
                        )
                    except (KeyError, IndexError):
                        message = str(data)

                raise MPRestError(
                    f"REST post query returned with error status code {response.status_code} "
                    f"on URL {response.url} with message:\n{message}"
                )

        except RequestException as ex:
            raise MPRestError(str(ex))

    def _query_open_data(
        self, bucket: str, key: str, decoder: Callable | None = None
    ) -> tuple[list[dict] | list[bytes], int]:
        """Query and deserialize Materials Project AWS open data s3 buckets.

        Args:
            bucket (str): Materials project bucket name
            key (str): Key for file including all prefixes
            decoder(Callable or None): Callable used to deserialize data.
                Defaults to mp_api.core.utils.load_json

        Returns:
            dict: MontyDecoded data
        """
        try:
            byio = BytesIO()
            self.s3_client.download_fileobj(bucket, key, byio)
            byio.seek(0)
            if (file_data := byio.read()).startswith(b"\x1f\x8b"):
                file_data = gzip.decompress(file_data)
            byio.close()

            decoder = decoder or load_json

            if "jsonl" in key:
                decoded_data = [decoder(jline) for jline in file_data.splitlines()]
            else:
                decoded_data = decoder(file_data)
                if not isinstance(decoded_data, list):
                    decoded_data = [decoded_data]

            raise_error = not decoded_data or len(decoded_data) == 0

        except ClientError:
            # No such object exists
            raise_error = True

        if raise_error:
            raise MPRestError(f"No object found: s3://{bucket}/{key}")

        return decoded_data, len(decoded_data)  # type: ignore

    def _get_delta_table(
        self,
        bucket: str,
        prefix: str,
        connector: str = "s3a",
        label: str | None = None,
        refresh: bool = False,
    ) -> tuple[str, DeltaTable]:
        """Either create a new DeltaTable, or retrieve a cached one.

        If creating a new DeltaTable, will also register it in self.delta_catalog

        Args:
            bucket (str) : name of the bucket in S3
            prefix (str) : name of the prefix in S3
            connector (str) : s3, s3n, s3a (default), or other
                valid Hadoop connector string.
            label (str or None) : optional label (SQL table name) for the
                table in the catalog. If `None`, will be gleaned from the URI
            refresh (bool) : if the table is already cached, reload its
                snapshot to the latest version first

        Returns:
            str : the table name in the catalog
            DeltaTable : If one exists at the specified bucket / prefix,
                will retrieve the cached instance.
        """
        delta_timeout = f"{self.timeout * 3}s"
        full_key = f"{bucket}/{prefix}"
        qb_label = label or full_key.replace("/", "_").replace("-", "_")

        uri = f"{connector}://{full_key}"
        if not uri.endswith("/"):
            uri += "/"

        stored_label, delta_table = self.delta_catalog.get_table(
            uri,
            qb_label,
            storage_options={
                "AWS_SKIP_SIGNATURE": "true",
                "AWS_REGION": "us-east-1",
                "timeout": delta_timeout,
                "connect_timeout": delta_timeout,
                "pool_idle_timeout": delta_timeout,
                "retry_delay": "3",
                "max_retries": f"{MAPI_CLIENT_SETTINGS.MAX_RETRIES}",
            },
            refresh=refresh,
        )

        if stored_label != qb_label:
            logger.debug(
                f"DeltaTable with URI {uri} already found with different label: "
                f"Stored label = {stored_label}; submitted label {qb_label}. "
                "Using stored DeltaTable."
            )

        return stored_label, delta_table

    def _query_delta_single(self, query: str, label: str | None = None) -> pa.Table:
        """Execute a SQL query against a registered Delta table.

        If `label` is given and the query fails because a file in the cached
        snapshot no longer exists (e.g. the remote table was vacuumed), only
        that table is reloaded and the query is retried once.

        Wraps the query execution in a try/except to provide a more
        actionable error message when the underlying Delta query engine
        fails (e.g., due to network timeouts, missing tables, or
        malformed queries).

        Args:
            query (str): A SQL query string compatible with the
                QueryBuilder engine.
            label (str or None): The registered table the query reads from,
                as returned by `_get_delta_table`. Required for retries.

        Returns:
            pa.Table: The query result as a PyArrow Table.

        Raises:
            MPRestError: If query execution fails for any reason,
                including network timeouts, connectivity issues, or
                invalid queries. Inspect the chained exception for
                the underlying cause.
        """
        try:
            return self.delta_catalog.execute(query, label=label)
        except Exception as e:
            refreshed = any(
                "after refreshing" in note for note in getattr(e, "__notes__", [])
            )
            hint = (
                f"The DeltaTable '{label}' was refreshed and the query retried once."
                if refreshed
                else (
                    "If this is a timeout error, try increasing the 'timeout' "
                    f"parameter on MPRester (current value: {self.timeout}s)."
                )
            )
            raise MPRestError(f"Failed to retrieve object due to: {e}. {hint}") from e

    def _s3_location(self) -> tuple[str, str, str]:
        """Where this rester's full dataset lives on S3.

        Returns:
            tuple of the collection name (e.g. "chemenv"), the bucket
            (e.g. "materialsproject-build") and the prefix
            (e.g. "collections/chemenv")
        """
        if self.suffix in S3_COLLECTION_NAMES:
            suffix = S3_COLLECTION_NAMES[self.suffix]
        elif "/" not in self.suffix:
            suffix = self.suffix
        else:
            infix, suffix = self.suffix.split("/", 1)
            suffix = infix if suffix == "core" else suffix
            suffix = suffix.replace("_", "-")

        if "tasks" in suffix:
            bucket_suffix, prefix = ("parsed", "core/tasks")
        elif suffix in STATIC_COLLECTIONS:
            bucket_suffix = "build"
            prefix = f"static-collections/{suffix}"
        else:
            # TODO: remove once all collections are migrated to delta-backed format
            bucket_suffix = "build"
            prefix = f"collections/{suffix}"

        return suffix, f"materialsproject-{bucket_suffix}", prefix

    def available_db_versions(self) -> list[str]:
        """Database versions available for this collection's full dataset on S3.

        Read from the DeltaTable's log, no data is downloaded. Any of these
        can be pinned with `MPRester(db_version=...)` to download that
        version of the dataset.

        Returns:
            list of str : sorted database versions, e.g. ["2026.04.13", "2026.09.28"]

        Raises:
            MPRestError: if this collection isn't delta-backed, or its
                dataset isn't partitioned by database version.
        """
        if not self.delta_backed:
            raise MPRestError(
                f"{self.suffix} is not backed by a DeltaTable on S3, "
                "so it has no database versions to list."
            )
        _, bucket, prefix = self._s3_location()
        label, _ = self._get_delta_table(bucket, prefix, refresh=True)
        counts = self.delta_catalog.partition_row_counts(label)
        if counts is None:
            raise MPRestError(
                f"The {self.suffix} dataset is not partitioned by database version, "
                "it always contains the latest data."
            )
        return sorted(to_db_version(v) for v in counts)

    @staticmethod
    def _resolve_db_version(
        requested: str, available: dict[str, int] | Iterable[str], collection: str
    ) -> str:
        """Turn a requested database version into a partition value of a table.

        Args:
            requested (str) : normalized database version, or "latest"
            available (dict or iterable of str) : partition values in the table
            collection (str) : collection name, for messages

        Returns:
            str : partition value, e.g. "2026-04-13"

        Raises:
            MPRestError: if no version is requested, the table has no versions,
                or the requested version isn't in the table.
        """
        versions = sorted(available)
        if not requested:
            raise MPRestError(
                f"The {collection} dataset is partitioned by database version, "
                "but no database version is set. Pass `db_version` to MPRester."
            )
        if not versions:
            raise MPRestError(f"The {collection} dataset has no published versions.")
        if requested == LATEST_DB_VERSION:
            # Versions are dates (with optional -postN suffixes), so they sort as text
            return versions[-1]
        version = to_partition_version(requested)
        if version not in versions:
            raise MPRestError(
                f"Database version {to_db_version(version)} is not available "
                f"for the {collection} dataset. Available versions: "
                f"{', '.join(to_db_version(v) for v in versions)}."
            )
        return version

    def _check_rest_db_version(self, db_version: str) -> None:
        """Raise if a per-call db_version can't be served by the REST API.

        Filtered queries go to the REST API, which only serves the current
        database version.

        Args:
            db_version (str) : database version requested for this call

        Raises:
            MPRestError: if `db_version` isn't the version the API serves
        """
        requested = _normalize_db_version(db_version)
        current = self.current_db_version
        if requested == LATEST_DB_VERSION:
            # Compare with the newest version on S3
            try:
                requested = self.available_db_versions()[-1]
            except Exception:
                return  # single-version dataset: "latest" is the current data
        if current and requested != current:
            raise MPRestError(
                f"db_version={db_version!r} only applies to full dataset downloads "
                "(a search with no filters). Filtered queries are answered by the "
                f"API, which serves database version {current}. Remove the filters "
                "to download that version, then filter it locally."
            )

    def _query_delta_backed(
        self,
        bucket: str,
        prefix: str,
        access_controlled: bool = True,
        timeout: int | None = None,
        label: str | None = None,
        db_version: str | None = None,
    ) -> dict[str, Any]:
        """Download a full dataset from a DeltaTable on S3 into the local cache.

        Tables partitioned by `version` hold one partition per database
        build. Only the partition for `db_version` (default `self.db_version`)
        is downloaded, and it
        is added to a local DeltaTable with the same partitioning, so several
        versions can be kept side by side. If the local table already has
        that version, it is returned without any network access, unless
        `self.force_renew` is set, in which case only that version is
        downloaded again and replaced.

        Data is written in chunks (see `DATASET_FLUSH_THRESHOLD`) to bound
        memory, and the chunks are committed to the local table in one
        transaction at the end, so an interrupted download never leaves a
        partial version visible.

        Args:
            bucket (str) : S3 OpenData bucket
            prefix (str) : S3 object prefix
            access_controlled (bool): whether or not table has access controlled data
            timeout (int or None) : timeout on getting access-controlled groups
            label (str or None) : label of the table in QueryBuilder
            db_version (str or None) : database version to download for this
                call, e.g. "2026.04.13" or "latest". Defaults to `self.db_version`.

        Returns:
            dict of str to Any
        """
        override = _normalize_db_version(db_version)
        requested = override or self.db_version
        # just in case
        prefix = prefix.rstrip("/")
        collection = prefix.split("/")[-1]

        target_path = str(
            self.local_dataset_cache.joinpath(
                f"{bucket.split('materialsproject-')[1]}/{prefix}"
            )
        )

        # Load the remote table to learn its partitioning and versions.
        # Full downloads are one-off, always start from the latest snapshot.
        tbl_lbl, tbl = self._get_delta_table(bucket, prefix, label=label, refresh=True)
        version_counts = self.delta_catalog.partition_row_counts(tbl_lbl)
        versioned = version_counts is not None

        version: str | None = None
        if versioned:
            version = self._resolve_db_version(
                requested,
                version_counts,
                collection,  # type: ignore[arg-type]
            )
        elif override:
            logger.warning(
                f"The {collection} dataset has a single version, ignoring "
                f"db_version={db_version!r}."
            )

        def _dataset() -> dict[str, Any]:
            return {
                "data": MPDataset(
                    path=target_path,
                    document_model=self.document_model,
                    use_document_model=self.use_document_model,
                    version=version,
                )
            }

        version_note = f" (v{to_db_version(version)})" if version else ""
        local = self._local_delta_table(target_path, versioned, collection)
        if local is not None and not self.force_renew:
            local_versions = {
                p.get("version") for p in local.partitions() if p.get("version")
            }
            if not versioned or version in local_versions:
                logger.warning(
                    f"Dataset for {collection}{version_note} already exists at "
                    f"{target_path}, returning existing dataset."
                )
                logger.info(
                    "Delete or move existing dataset or re-run search query with "
                    "MPRester(force_renew=True) to refresh local dataset.",
                )
                return _dataset()
            logger.info(
                f"Adding {collection}{version_note} to the existing local dataset at "
                f"{target_path}."
            )
        elif local is not None:
            logger.warning(
                f"Regenerating {collection}{version_note} at {target_path}..."
            )

        # Check if user has access to GNoMe
        has_gnome_access = bool(
            self._submit_requests(
                url=urljoin(self.base_endpoint, "materials/summary/"),
                criteria={
                    "batch_id": "gnome_r2scan_statics",
                    "_fields": "material_id",
                },
                use_document_model=False,
                num_chunks=1,
                chunk_size=1,
                timeout=timeout if timeout is not None else self.timeout,
                show_progress=False,
            )
            .get("meta", {})
            .get("total_doc", 0)
        )

        conditions = []
        if versioned:
            conditions.append(f"version = '{version}'")
        filter_access = access_controlled and not has_gnome_access
        if filter_access:
            if collection == "tasks":
                controlled_batch_str = ",".join(
                    [f"'{tag}'" for tag in self.access_controlled_batch_ids]
                )
                conditions.append(f"batch_id NOT IN ({controlled_batch_str})")
            else:
                conditions.append("builder_meta.license != 'BY-NC'")
        predicate = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        num_docs_needed = self._count_delta_docs(
            tbl_lbl,
            tbl,
            predicate,
            version_counts[version] if versioned else None,  # type: ignore[index]
            filter_access,
            f"{collection}{version_note}",
        )

        iterator = self.delta_catalog.execute_stream(
            f"SELECT * FROM {tbl_lbl} {predicate}"
        )

        # Every column except the partition column, in the document model's
        # order. The partition value goes in the directory name.
        schema = self._download_schema()
        if "version" in schema.names:
            schema = schema.remove(schema.get_field_index("version"))
        file_options = ds.ParquetFileFormat().make_write_options(compression="zstd")
        data_dir = (
            os.path.join(target_path, f"version={version}")
            if versioned
            else target_path
        )
        os.makedirs(data_dir, exist_ok=True)
        # Unique per download, so a retry never overwrites files the table uses
        run_tag = uuid.uuid4().hex[:8]
        added: list[AddAction] = []
        partition_values = {"version": version} if versioned else {}

        def _record(written_file: Any) -> None:
            added.append(
                AddAction(
                    path=quote(
                        os.path.relpath(written_file.path, target_path), safe="/="
                    ),
                    size=os.path.getsize(written_file.path),
                    partition_values=partition_values,
                    modification_time=int(time.time() * 1000),
                    data_change=True,
                    stats=json.dumps({"numRecords": written_file.metadata.num_rows}),
                )
            )

        def _flush(accumulator: list[pa.RecordBatch], group: int) -> None:
            # somewhere post datafusion 51.0.0 and arrow-rs 57.0.0
            # casts to *View types began, need to cast back to base schema
            # -> pyarrow is behind on implementation support for *View types
            chunk = (
                pa.Table.from_batches(accumulator)
                .select(schema.names)
                .cast(target_schema=schema)
            )
            ds.write_dataset(
                chunk,
                base_dir=data_dir,
                format="parquet",
                basename_template=f"group-{group}-{run_tag}-" + "part-{i}.zstd.parquet",
                existing_data_behavior="overwrite_or_ignore",
                max_rows_per_group=1024,
                file_options=file_options,
                file_visitor=_record,
            )

        docs = self._docs_description
        try:
            with progress_bar(
                f"Retrieving DeltaTable-backed {docs}{version_note}",
                total=num_docs_needed,
                enabled=not self.mute_progress_bars,
                summary=f"Downloaded {{completed:,}} {docs}{version_note} to {target_path}",
            ) as pbar:
                group = 1
                size = 0
                accumulator: list[pa.RecordBatch] = []
                for rb in iterator:
                    accumulator.append(rb)
                    size += rb.get_total_buffer_size()
                    pbar.update(rb.num_rows)

                    if size >= MAPI_CLIENT_SETTINGS.DATASET_FLUSH_THRESHOLD:
                        with status(
                            f"Writing {docs} to disk...",
                            enabled=not self.mute_progress_bars,
                        ):
                            _flush(accumulator, group)
                        group += 1
                        size = 0
                        accumulator.clear()

                # Writing the last chunk and committing can take a while,
                # replace the (full) bar with a spinner meanwhile.
                pbar.hide()
                with status(
                    f"Writing {docs}{version_note} to the local DeltaTable...",
                    enabled=not self.mute_progress_bars,
                ):
                    if accumulator:
                        _flush(accumulator, group)
                    self._commit_delta_download(
                        target_path, local, schema, added, version, versioned
                    )
        except BaseException:
            # The files were never committed, so the table doesn't reference them
            for action in added:
                try:
                    os.remove(os.path.join(target_path, unquote(action.path)))
                except OSError:
                    logger.warning(
                        f"Could not remove uncommitted file {action.path} in {target_path}."
                    )
            raise

        if not (pbar.shown and pbar.completed):
            # The progress summary (which includes the path) wasn't printed,
            # e.g. muted progress bars or non-interactive output
            logger.info(
                f"Dataset for {collection}{version_note} written to {target_path}"
            )
        logger.debug(
            "Consult the delta-rs and pyarrow documentation for advanced usage: "
            "delta-io.github.io/delta-rs, arrow.apache.org/docs/python"
        )
        return _dataset()

    def _download_schema(self) -> pa.Schema:
        """Arrow schema of the data written by a full download.

        Defaults to the document model's. Override when the model has fields
        that aren't stored in the S3 table (e.g. fields added by a search).
        """
        return pa.schema(arrowize(self.document_model))

    def _local_delta_table(
        self, target_path: str, versioned: bool, collection: str
    ) -> DeltaTable | None:
        """Open the local copy of a dataset, if there is one.

        If the local copy was made by an older client and doesn't match the
        remote layout (not a DeltaTable, or not partitioned by version when
        the remote is), it can't be added to. With `force_renew` it is
        deleted so the download starts fresh; otherwise an error is raised.

        Args:
            target_path (str) : local dataset directory
            versioned (bool) : whether the remote table is partitioned by version
            collection (str) : collection name, for messages

        Returns:
            the local DeltaTable, or None if there is none (or it was removed)
        """
        if not os.path.isdir(target_path) or not os.listdir(target_path):
            return None

        reason = None
        if not DeltaTable.is_deltatable(target_path):
            reason = "is not a DeltaTable"
        else:
            local = DeltaTable(target_path)
            local_versioned = "version" in local.metadata().partition_columns
            if local_versioned == versioned:
                return local
            reason = (
                "is not partitioned by database version"
                if versioned
                else "is partitioned by database version, but the remote dataset isn't"
            )

        if not self.force_renew:
            raise MPRestError(
                f"The local {collection} dataset at {target_path} {reason}, likely "
                "because it was downloaded by an older version of mp-api. Delete or "
                "move it, or re-run with MPRester(force_renew=True) to replace it."
            )
        logger.warning(
            f"Removing the local {collection} dataset at {target_path}: it {reason}."
        )
        shutil.rmtree(target_path)
        return None

    def _count_delta_docs(
        self,
        tbl_lbl: str,
        tbl: DeltaTable,
        predicate: str,
        version_rows: int | None,
        filter_access: bool,
        description: str,
    ) -> int | None:
        """Number of documents a full download will fetch, for the progress bar.

        Without an access filter this is read from the Delta log (instant).
        With one, the rows have to be counted on S3, which can be slow for
        large tables; a status line is shown meanwhile.

        Args:
            tbl_lbl (str) : label of the remote table in the catalog
            tbl (DeltaTable) : the remote table
            predicate (str) : WHERE clause of the download query, or ""
            version_rows (int or None) : rows in the requested version, from
                the log, or None if the table isn't versioned
            filter_access (bool) : whether access-controlled rows are excluded
            description (str) : what's being counted, for the status line

        Returns:
            int, or None if counting failed (the bar then has no total)
        """
        if not filter_access:
            return version_rows if version_rows is not None else tbl.count()

        try:
            with status(
                f"Counting {description} documents (excluding access-controlled "
                "entries), this can take a while...",
                enabled=not self.mute_progress_bars,
            ):
                result = self.delta_catalog.execute(
                    f"SELECT COUNT(*) AS n FROM {tbl_lbl} {predicate}", label=tbl_lbl
                )
            return int(result.column("n")[0].as_py())
        except Exception as exc:
            logger.warning(
                f"Could not count {description} documents, downloading without a total: {exc}"
            )
            return None

    @staticmethod
    def _commit_delta_download(
        target_path: str,
        local: DeltaTable | None,
        schema: pa.Schema,
        added: list[AddAction],
        version: str | None,
        versioned: bool,
    ) -> None:
        """Commit downloaded files to the local DeltaTable in one transaction.

        Creates the table if there is none. Otherwise appends a new version
        partition, or, if the version (or, for unversioned tables, the
        table) is already there, replaces it.

        Args:
            target_path (str) : local dataset directory
            local (DeltaTable or None) : the existing local table, if any
            schema (pa.Schema) : schema of the data files (no partition column)
            added (list of AddAction) : the files written by this download
            version (str or None) : partition value of the downloaded version
            versioned (bool) : whether the table is partitioned by version
        """
        partition_by = ["version"] if versioned else None
        table_schema = Schema.from_arrow(
            schema.append(pa.field("version", pa.string())) if versioned else schema
        )
        if local is None:
            create_table_with_add_actions(
                target_path,
                table_schema,
                added,
                mode="error",
                partition_by=partition_by,
            )
            return

        if not versioned:
            local.create_write_transaction(added, mode="overwrite", schema=table_schema)
        elif version in {p.get("version") for p in local.partitions()}:
            local.create_write_transaction(
                added,
                mode="overwrite",
                schema=table_schema,
                partition_by=partition_by,
                partition_filters=[("version", "=", version)],  # type: ignore[list-item]
            )
        else:
            local.create_write_transaction(
                added, mode="append", schema=table_schema, partition_by=partition_by
            )
            return

        # A replaced version's old files are no longer in the table, delete
        # them now rather than keeping two copies on disk.
        local.update_incremental()
        removed = local.vacuum(
            retention_hours=0, dry_run=False, enforce_retention_duration=False
        )
        if removed:
            logger.debug(f"Removed {len(removed)} replaced files from {target_path}.")

    def _query_resource(
        self,
        criteria: dict | None = None,
        fields: list[str] | None = None,
        suburl: str | None = None,
        use_document_model: bool | None = None,
        num_chunks: int | None = None,
        chunk_size: int | None = None,
        timeout: int | None = None,
        show_progress: bool | None = None,
        db_version: str | None = None,
    ) -> dict[str, Any]:
        """Query the endpoint for a Resource containing a list of documents
        and meta information about pagination and total document count.

        For the end-user, methods .search() and .count() are intended to be
        easier to use.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute
            num_chunks: Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size: Number of data entries per chunk.
            timeout (float or None): Time in seconds to wait until a request timeout error is thrown
            show_progress (bool or None): Whether to show progress bars for this call.
                If None, defers to `not self.mute_progress_bars`.
            db_version (str or None): Database version for this call, e.g. "2026.04.13"
                or "latest". Only full downloads (no filters) can use a version other
                than the one the API serves. Defaults to `self.db_version`.

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """
        if use_document_model is None:
            use_document_model = self.use_document_model
        if show_progress is None:
            show_progress = not self.mute_progress_bars

        timeout = self.timeout if timeout is None else timeout

        criteria = {k: v for k, v in (criteria or {}).items() if v is not None}

        # Query s3 if no query is passed and all documents are asked for
        # TODO also skip fields set to same as their default
        no_query = not {field for field in criteria if field[0] != "_"}
        query_s3 = no_query and num_chunks is None

        if db_version and not query_s3:
            self._check_rest_db_version(db_version)

        if fields:
            if isinstance(fields, str):
                fields = [fields]

            if not suburl:
                invalid_fields = [
                    f for f in fields if f.split(".", 1)[0] not in self.available_fields
                ]
                if invalid_fields:
                    raise MPRestError(
                        f"invalid fields requested: {invalid_fields}. Available fields: {self.available_fields}"
                    )

            criteria["_fields"] = ",".join(fields)

        try:
            url = validate_endpoint(self.endpoint, suffix=suburl)

            if query_s3:
                docs_name = self._docs_description
                pbar_message = f"Retrieving {docs_name}"
                pbar_summary = f"Retrieved {{completed:,}} {docs_name}"

                suffix, bucket, prefix = self._s3_location()

                if self.delta_backed:
                    return self._query_delta_backed(
                        bucket=bucket,
                        prefix=prefix,
                        access_controlled=suffix in CONTROLLED_COLLECTIONS,
                        timeout=timeout,
                        db_version=db_version,
                    )

                if db_version:
                    logger.warning(
                        f"The {suffix} dataset has a single version, ignoring "
                        f"db_version={db_version!r}."
                    )

                # Paginate over all entries in the bucket.
                # TODO: change when a subset of entries needed from DB
                paginator = self.s3_client.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

                keys = [
                    obj["Key"]
                    for page in pages
                    for obj in page.get("Contents", [])
                    if obj.get("Key") and "manifest" not in obj["Key"]
                ]

                if len(keys) < 1:
                    return self._submit_requests(
                        url=url,
                        criteria=criteria,
                        use_document_model=use_document_model,
                        num_chunks=num_chunks,
                        chunk_size=chunk_size,
                        timeout=timeout,
                        show_progress=show_progress,
                    )

                if fields:
                    mp_warning(
                        "Ignoring `fields` argument: All fields are always included when no query is provided.",
                        stacklevel=2,
                    )

                # Multithreaded function inputs
                s3_params_list = {
                    key: {
                        "bucket": bucket,
                        "key": key,
                    }
                    for key in keys
                }

                num_docs_needed = int(self.count())
                with progress_bar(
                    pbar_message,
                    total=num_docs_needed,
                    enabled=show_progress,
                    summary=pbar_summary,
                ) as pbar:
                    unzipped_chunks = [
                        docs
                        for docs, _, _ in self._multi_thread(
                            self._query_open_data,
                            list(s3_params_list.values()),
                            pbar,
                        )
                    ]

                _chunks = chain.from_iterable(unzipped_chunks)
                data: dict[str, Any] = {
                    "data": (
                        _convert_to_model(_chunks, self.document_model)
                        if self.document_model and use_document_model
                        else list(_chunks)
                    ),
                    "meta": {},
                }

            else:
                data = self._submit_requests(
                    url=url,
                    criteria=criteria,
                    use_document_model=not query_s3 and use_document_model,
                    num_chunks=num_chunks,
                    chunk_size=chunk_size,
                    timeout=timeout,
                    show_progress=show_progress,
                )
            return data

        except RequestException as ex:
            raise MPRestError(str(ex))

    def _submit_requests(
        self,
        url: str,
        criteria: dict[str, Any],
        use_document_model: bool,
        chunk_size: int | None,
        num_chunks: int | None = None,
        timeout: int | None = None,
        max_batch_size: int = 100,
        norecur: bool = False,
        show_progress: bool | None = None,
    ) -> dict:
        """Handle submitting requests sequentially with pagination.

        If criteria contains comma-separated parameters (except those that are naturally comma-separated),
        split them into multiple sequential requests and combine results.

        Arguments:
            url (str): url used to make request
            criteria (dict of str): dictionary of criteria to filter down
            use_document_model (bool): whether to use the document model
            num_chunks (int or None): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int or None): Number of data entries per chunk.
            timeout (int or None): Time in seconds to wait until a request timeout error is thrown
            max_batch_size (int) : Maximum size of a batch when retrieving batches in parallel
            norecur (bool) : Whether to forbid recursive splitting of a query field
                when a direct query fails
            show_progress (bool or None): Whether to show progress bars for this call.
                If None, defers to `not self.mute_progress_bars`.

        Returns:
            Dictionary containing data and metadata
        """
        if show_progress is None:
            show_progress = not self.mute_progress_bars

        # Parameters that naturally support comma-separated values and should NOT be split
        no_split_params = {
            "elements",
            "exclude_elements",
            "possible_species",
            "coordination_envs",
            "coordination_envs_anonymous",
            "has_props",
            "gb_plane",
            "rotation_axis",
            "keywords",
            "substrate_orientation",
            "film_orientation",
            "synthesis_type",
            "operations",
            "condition_mixing_device",
            "condition_mixing_media",
            "condition_heating_atmosphere",
            "_fields",
            "formula",
            "chemsys",
        }

        with ExitStack() as stack:
            return self._submit_requests_inner(
                stack,
                url=url,
                criteria=criteria,
                use_document_model=use_document_model,
                chunk_size=chunk_size,
                num_chunks=num_chunks,
                timeout=timeout,
                max_batch_size=max_batch_size,
                norecur=norecur,
                show_progress=show_progress,
                no_split_params=no_split_params,
            )

    def _submit_requests_inner(
        self,
        stack: ExitStack,
        url: str,
        criteria: dict[str, Any],
        use_document_model: bool,
        chunk_size: int | None,
        num_chunks: int | None,
        timeout: int | None,
        max_batch_size: int,
        norecur: bool,
        show_progress: bool,
        no_split_params: set[str],
    ) -> dict:
        """Body of `_submit_requests`; `stack` owns the progress bar's lifetime."""
        docs_name = self._docs_description
        pbar: ProgressHandle | None = None

        def open_bar() -> ProgressHandle:
            # Started before the first request (spinner until the total is
            # known), closed when `stack` exits, including on errors.
            return stack.enter_context(
                progress_bar(
                    f"Retrieving {docs_name}",
                    total=None,
                    enabled=show_progress,
                    summary=f"Retrieved {{completed:,}} {docs_name}",
                )
            )

        # Check if we need to split any comma-separated parameters
        split_param = None
        split_values = []
        total_num_docs = 0  # Initialize before try/else blocks
        data_chunks = []
        total_data_len = 0

        for key, value in criteria.items():
            if (
                isinstance(value, str)
                and "," in value
                and key not in no_split_params
                and not key.startswith("_")
            ):
                split_param = key
                split_values = value.split(",")
                break

        # If we found a parameter to split, try the request first and only split on error
        if split_param and len(split_values or []) > 1:
            try:
                # First, try the request with all values as-is
                initial_criteria = copy(criteria)
                data, total_num_docs = self._submit_request_and_process(
                    url=url,
                    verify=True,
                    params=initial_criteria,
                    use_document_model=use_document_model,
                    timeout=timeout,
                )

                # If successful, continue with normal pagination
                data_chunks = [data["data"]]
                total_data: dict[str, Any] = {"data": []}
                total_data_len = len(data["data"])

                if "meta" in data:
                    total_data["meta"] = data["meta"]

                # Continue with pagination if needed (handled below)

            except MPRestError as e:
                # If we get 422 or 414 error, split into batches
                if not norecur and any(
                    trace in str(e)
                    for trace in (
                        "422",
                        "414",
                    )
                ):
                    total_data = {"data": []}
                    total_num_docs = 0
                    data_chunks = []

                    # Batch the split values to reduce number of requests
                    # Use batches of up to 100 values to balance URL length and request count
                    batch_size = min(len(split_values), max_batch_size)
                    num_batches = ceil(len(split_values) / batch_size)

                    with progress_bar(
                        f"Retrieving {len(split_values)} {split_param} values "
                        f"in {num_batches} batches",
                        total=num_batches,
                        enabled=show_progress,
                        unit="batches",
                        summary=f"Retrieved {len(split_values)} {split_param} values "
                        "in {completed} batches",
                    ) as pbar:
                        for batch in batched(split_values, batch_size):
                            split_criteria = copy(criteria)
                            split_criteria[split_param] = ",".join(batch)

                            # Recursively call _submit_requests with the batch
                            # This will trigger another split if the batch is still too large
                            result = self._submit_requests(
                                url=url,
                                criteria=split_criteria,
                                use_document_model=use_document_model,
                                chunk_size=chunk_size,
                                num_chunks=num_chunks,
                                timeout=timeout,
                                norecur=len(batch) <= max_batch_size,
                                show_progress=show_progress,
                            )

                            data_chunks.append(result["data"])
                            if "meta" in result:
                                total_data["meta"] = result["meta"]
                                total_num_docs += result["meta"].get("total_doc", 0)

                            pbar.update(1)

                    total_data["data"] = list(chain.from_iterable(data_chunks))

                    # Update total_doc if we have meta
                    if "meta" in total_data:
                        total_data["meta"]["total_doc"] = total_num_docs

                    return total_data
                else:
                    # Re-raise other errors
                    raise
        else:
            # No splitting needed - get first page
            pbar = open_bar()
            total_data = {"data": []}
            initial_criteria = copy(criteria)
            if isinstance(
                initial_criteria.get("_page"), int
            ) and not initial_criteria.get("_per_page"):
                initial_criteria["_per_page"] = initial_criteria.get("_limit")
            data, total_num_docs = self._submit_request_and_process(
                url=url,
                verify=True,
                params=initial_criteria,
                use_document_model=use_document_model,
                timeout=timeout,
            )

            data_chunks = [data["data"]]
            total_data_len = len(data["data"])

            if "meta" in data:
                total_data["meta"] = data["meta"]

        # otherwise, paginate sequentially
        if chunk_size is None or chunk_size < 1:
            raise ValueError(
                "A positive chunk size must be provided to enable pagination"
            )

        # Get max number of response pages
        max_pages = (
            num_chunks if num_chunks is not None else ceil(total_num_docs / chunk_size)
        )

        # Get total number of docs needed
        num_docs_needed = min((max_pages * chunk_size), total_num_docs)

        if pbar is None:
            # first request succeeded on the split path
            pbar = open_bar()
        initial_data_length = total_data_len
        pbar.total = num_docs_needed
        pbar.update(min(initial_data_length, num_docs_needed))

        # If we have all the results in a single page, return directly
        if initial_data_length >= num_docs_needed or num_chunks == 1:
            new_total_data = copy(total_data)
            new_total_data["data"] = list(chain.from_iterable(data_chunks))[
                :num_docs_needed
            ]
            return new_total_data

        # Warning to select specific fields only for many results
        if criteria.get("_all_fields", False) and (total_num_docs / chunk_size > 10):
            mp_warning(
                f"Use the 'fields' argument to select only fields of interest to speed "
                f"up data retrieval for large queries. "
                f"Choose from: {self.available_fields}",
                stacklevel=2,
            )

        # Paginate through remaining results
        skip = criteria.get("_limit") or chunk_size
        remaining_docs = total_num_docs - initial_data_length

        while total_data_len < num_docs_needed and remaining_docs > 0:
            page_criteria = copy(criteria)
            page_criteria["_skip"] = skip

            # Determine limit for this request
            docs_still_needed = num_docs_needed - total_data_len
            page_criteria["_limit"] = min(chunk_size, docs_still_needed, remaining_docs)

            data, _ = self._submit_request_and_process(
                url=url,
                verify=True,
                params=page_criteria,
                use_document_model=use_document_model,
                timeout=timeout,
            )

            data_chunks.append(data["data"])
            chunk_len = len(data["data"])
            total_data_len += chunk_len
            pbar.update(chunk_len)

            skip += page_criteria["_limit"]
            remaining_docs -= chunk_len

            # Break if we didn't get any data (shouldn't happen, but safety check)
            if chunk_len == 0:
                break

        total_data["data"] = list(chain.from_iterable(data_chunks))

        return total_data

    # this is here as a separate function to allow for multithreading when querying s3 buckets
    # which is necessary to speed up retrieval of large data dumps
    def _multi_thread(
        self,
        func: Callable,
        params_list: list[dict],
        progress_bar: ProgressHandle | None = None,
    ) -> list[tuple[Any, int, int]]:
        """Handles setting up a threadpool and sending parallel requests.

        Arguments:
            func (Callable): Callable function to multi
            params_list (list): list of dictionaries containing url and params for each request
            progress_bar (ProgressHandle): progress bar to update with progress

        Returns:
            Tuples with data, total number of docs in matching the query in the database,
            and the index of the criteria dictionary in the provided parameter list
        """
        return_data = []

        params_gen = iter(
            params_list
        )  # Iter necessary for islice to keep track of what has been accessed

        params_ind = 0

        with ThreadPoolExecutor(
            max_workers=MAPI_CLIENT_SETTINGS.NUM_PARALLEL_REQUESTS  # type: ignore
        ) as executor:
            # Get list of initial futures defined by max number of parallel requests
            futures = set()

            for params in itertools.islice(
                params_gen,
                MAPI_CLIENT_SETTINGS.NUM_PARALLEL_REQUESTS,  # type: ignore
            ):
                future = executor.submit(
                    func,
                    **params,
                )

                future.crit_ind = params_ind  # type: ignore
                futures.add(future)
                params_ind += 1

            while futures:
                # Wait for at least one future to complete and process finished
                finished, futures = wait(futures, return_when=FIRST_COMPLETED)

                for future in finished:
                    data, subtotal = future.result()

                    if progress_bar is not None:
                        if isinstance(data, dict):
                            size = len(data["data"])
                        elif isinstance(data, list):
                            size = len(data)
                        else:
                            size = 1
                        progress_bar.update(size)

                    return_data.append((data, subtotal, future.crit_ind))  # type: ignore

                # Populate more futures to replace finished
                for params in itertools.islice(params_gen, len(finished)):
                    new_future = executor.submit(
                        func,
                        **params,
                    )

                    new_future.crit_ind = params_ind  # type: ignore
                    futures.add(new_future)
                    params_ind += 1

        return return_data

    def _submit_request_and_process(
        self,
        url: str,
        verify: bool,
        params: dict,
        use_document_model: bool,
        timeout: int | None = None,
    ) -> tuple[dict, int]:
        """Submits GET request and handles the response.

        Arguments:
            url: URL to send request to
            verify: whether to verify the server's TLS certificate
            params: dictionary of parameters to send in the request
            use_document_model: if None, will defer to the self.use_document_model attribute
            timeout: Time in seconds to wait until a request timeout error is thrown

        Returns:
            Tuple with data and total number of docs in matching the query in the database.
        """
        try:
            response = self.session.get(
                url=url,
                verify=verify,
                params=params,
                timeout=timeout,
                headers=self.headers,
            )
        except requests.exceptions.ConnectTimeout:
            raise MPRestError(
                f"REST query timed out on URL {url}. Try again with a smaller request."
            )

        if response.status_code in [400]:
            raise MPRestError(
                f"The server does not support the request made to {response.url}. "
                "This may be due to an outdated mp-api package, or a problem with the query."
            )

        if response.status_code == 200:
            data = load_json(response.text)
            # other sub-urls may use different document models
            # the client does not handle this in a particularly smart way currently
            if self.document_model and use_document_model:
                data["data"] = _convert_to_model(
                    data["data"],
                    self.document_model,
                    requested_fields=(
                        params["_fields"].split(",")
                        if isinstance(params.get("_fields"), str)
                        else None
                    ),
                )

            meta_total_doc_num = data.get("meta", {}).get("total_doc", 1)

            return data, meta_total_doc_num

        else:
            try:
                data = load_json(response.text)["detail"]
            except (JSONDecodeError, KeyError):
                data = f"Response {response.text}"
            if isinstance(data, str):
                message = data
            else:
                try:
                    message = ", ".join(
                        f"{entry['loc'][1]} - {entry['msg']}" for entry in data
                    )
                except (KeyError, IndexError):
                    message = str(data)

            raise MPRestError(
                f"REST query returned with error status code {response.status_code} "
                f"on URL {response.url} with message:\n{message}"
            )

    def _query_resource_data(
        self,
        criteria: dict | None = None,
        fields: list[str] | None = None,
        suburl: str | None = None,
        use_document_model: bool | None = None,
        timeout: int | None = None,
    ) -> list[BaseModel] | list[dict]:
        """Query the endpoint for a list of documents without associated meta information. Only
        returns a single page of results.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute
            timeout: Time in seconds to wait until a request timeout error is thrown

        Returns:
            A list of documents
        """
        return self._query_resource(  # type: ignore
            criteria=criteria,
            fields=fields,
            suburl=suburl,
            use_document_model=use_document_model,
            chunk_size=1000,
            num_chunks=1,
        ).get("data")

    def _search(
        self,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
        db_version: str | None = None,
        **kwargs,
    ) -> list[BaseModel] | list[dict]:
        """A generic search method to retrieve documents matching specific parameters.

        Arguments:
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Set to False to only return specific fields of interest. This will
                significantly speed up data retrieval for large queries and help us by reducing
                load on the Materials Project servers. Set to True by default to reduce confusion,
                unless "fields" are set, in which case all_fields will be set to False.
            fields (list[str]): List of fields to project. When searching, it is better to only ask for
                the specific fields of interest to reduce the time taken to retrieve the documents. See
                 the available_fields property to see a list of fields to choose from.
            db_version (str): Database version to download when no filters are given (full
                dataset), e.g. "2026.04.13" or "latest". Defaults to the rester's version.
                See `available_db_versions()`.
            kwargs: Supported search terms, e.g. nelements_max=3 for the "materials" search API.
                Consult the specific API route for valid search terms.

        Returns:
            A list of documents.
        """
        # This method should be customized for each end point to give more user friendly,
        # documented kwargs.

        # If user specifies page, ensure only one chunk is returned
        if isinstance(kwargs.get("_page"), int) and num_chunks is None:
            num_chunks = 1
        return self._get_all_documents(
            kwargs,
            all_fields=all_fields,
            fields=fields,
            chunk_size=chunk_size,
            num_chunks=num_chunks,
            db_version=db_version,
        )

    def get_data_by_id(
        self,
        document_id: str,
        fields: list[str] | None = None,
    ) -> BaseModel | dict[str, Any] | None:
        warnings.warn(
            "get_data_by_id is deprecated and will be removed soon. Please use the search method instead.",
            FutureWarning,
            stacklevel=2,
        )

        if self.primary_key in [
            "material_id",
            "task_id",
            "battery_id",
            "spectrum_id",
            "thermo_id",
        ]:
            document_id = validate_ids([document_id])[0]

        if isinstance(fields, str):  # pragma: no cover
            fields = (fields,)  # type: ignore

        docs = self._search(
            **{self.primary_key + "s": document_id},
            num_chunks=1,
            chunk_size=1,
            all_fields=fields is None,
            fields=fields,
        )
        return docs[0] if docs else None

    def _get_all_documents(
        self,
        query_params,
        all_fields=True,
        fields=None,
        chunk_size=1000,
        num_chunks=None,
        db_version: str | None = None,
    ) -> list[BaseModel] | list[dict]:
        """Iterates over pages until all documents are retrieved. Displays
        progress bars. This method is designed to give a common
        implementation for the search_* methods on various endpoints. See
        materials endpoint for an example of this in use.
        """
        if chunk_size <= 0:
            raise MPRestError("Chunk size must be greater than zero")

        if isinstance(num_chunks, int) and num_chunks <= 0:
            raise MPRestError("Number of chunks must be greater than zero or None.")

        if all_fields and not fields:
            query_params["_all_fields"] = True

        query_params["_limit"] = chunk_size

        results = self._query_resource(
            query_params,
            fields=fields,
            chunk_size=chunk_size,
            num_chunks=num_chunks,
            db_version=db_version,
        )

        return results["data"]

    def count(self, criteria: dict | None = None) -> int:
        """Return a count of total documents.

        Args:
            criteria (dict | None): As in .search(). Defaults to None

        Returns:
            int : Count of total results
        """
        criteria = criteria or {}
        # do not waste cycles decoding, and don't show progress
        query_kwargs: dict[str, Any] = {
            "num_chunks": 1,
            "chunk_size": 1,
            "use_document_model": False,
            "show_progress": False,
        }
        results = self._query_resource(criteria=criteria, **query_kwargs)
        cnt = results["meta"]["total_doc"]

        no_query = not {field for field in criteria if field[0] != "_"}
        if no_query and hasattr(self, "search"):
            allowed_params = inspect.getfullargspec(self.search).args
            if "deprecated" in allowed_params:
                criteria["deprecated"] = True
                results = self._query_resource(criteria=criteria, **query_kwargs)
                cnt += results["meta"]["total_doc"]
                mp_warning(
                    "Omitting a query also includes deprecated documents in the results. "
                    "Make sure to post-filter them out.",
                    stacklevel=2,
                )

        if isinstance(cnt, str):
            raise MPRestError(f"Error counting documents: {cnt}")
        return cnt

    @property
    def available_fields(self) -> list[str]:
        if self.document_model is None:
            return ["Unknown fields."]
        return list(self.document_model.model_json_schema()["properties"].keys())  # type: ignore

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} {self.endpoint}>"

    def __str__(self):  # pragma: no cover
        if self.document_model is None:
            return self.__repr__()
        return (
            f"{self.__class__.__name__} connected to {self.endpoint}\n\n"
            f"Available fields: {', '.join(self.available_fields)}\n\n"
        )


class CoreRester(BaseRester):
    """Define a BaseRester with extra features for core resters.

    Enables lazy importing / initialization of sub resters
    provided in `_sub_resters`, which should be a map
    of endpoints names to LazyImport objects.

    """

    _sub_resters: dict[str, LazyImport] = {}

    def __init__(self, **kwargs):
        """Ensure that sub resters are unset on re-init."""
        super().__init__(**kwargs)
        self.sub_resters = {k: v.copy() for k, v in self._sub_resters.items()}

    def __getattr__(self, v: str):
        if v in self.sub_resters:
            if self.sub_resters[v]._obj is None:
                self.sub_resters[v](
                    api_key=self.api_key,
                    endpoint=self.base_endpoint,
                    include_user_agent=self.include_user_agent,
                    session=self.session,
                    use_document_model=self.use_document_model,
                    headers=self.headers,
                    mute_progress_bars=self.mute_progress_bars,
                    db_version=self.db_version,
                    local_dataset_cache=self.local_dataset_cache,
                    force_renew=self.force_renew,
                    delta_catalog=self.delta_catalog,
                )
            return self.sub_resters[v]
        raise AttributeError(f"{self.__class__} has no attribute {v}")

    def __dir__(self):
        return dir(self.__class__) + list(self._sub_resters)
