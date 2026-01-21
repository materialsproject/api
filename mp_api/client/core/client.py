"""This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

from __future__ import annotations

import gzip
import inspect
import itertools
import os
import platform
import sys
import warnings
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from copy import copy
from functools import cache
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from json import JSONDecodeError
from math import ceil
from typing import TYPE_CHECKING, ForwardRef, Optional, get_args
from urllib.parse import quote

import boto3
import requests
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
from emmet.core.utils import jsanitize
from pydantic import BaseModel, create_model
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from tqdm.auto import tqdm
from urllib3.util.retry import Retry

from mp_api.client.core.exceptions import MPRestError
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS
from mp_api.client.core.utils import (
    load_json,
    validate_api_key,
    validate_endpoint,
    validate_ids,
)

try:
    import flask
except ImportError:
    flask = None

if TYPE_CHECKING:
    from typing import Any, Callable

    from pydantic.fields import FieldInfo

    from mp_api.client.core.utils import LazyImport

try:
    __version__ = version("mp_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION")


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


class BaseRester:
    """Base client class with core stubs."""

    suffix: str = ""
    document_model: type[BaseModel] | None = None
    primary_key: str = "material_id"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        include_user_agent: bool = True,
        session: requests.Session | None = None,
        s3_client: Any | None = None,
        debug: bool = False,
        use_document_model: bool = True,
        timeout: int = 20,
        headers: dict | None = None,
        mute_progress_bars: bool = MAPI_CLIENT_SETTINGS.MUTE_PROGRESS_BARS,
        **kwargs,
    ):
        """Initialize the REST API helper class.

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
            s3_client: boto3 S3 client object with which to connect to the object stores.ct to the object stores.ct to the object stores.
            debug: if True, print the URL for every request
            use_document_model: If False, skip the creating the document model and return data
                as a dictionary. This can be simpler to work with but bypasses data validation
                and will not give auto-complete for available fields.
            timeout: Time in seconds to wait until a request timeout error is thrown
            headers: Custom headers for localhost connections.
            mute_progress_bars: Whether to disable progress bars.
            **kwargs: access to legacy kwargs that may be in the process of being deprecated
        """
        self.api_key = validate_api_key(api_key)
        self.base_endpoint = validate_endpoint(endpoint)
        self.endpoint = validate_endpoint(endpoint, suffix=self.suffix)

        self.debug = debug
        self.include_user_agent = include_user_agent
        self.use_document_model = use_document_model
        self.timeout = timeout
        self.headers = headers or {}
        self.mute_progress_bars = mute_progress_bars
        self.db_version = BaseRester._get_database_version(self.base_endpoint)

        self._session = session
        self._s3_client = s3_client

        if "monty_decode" in kwargs:
            warnings.warn(
                "Ignoring `monty_decode`, as it is no longer a supported option in `mp_api`."
                "The client by default returns results consistent with `monty_decode=True`."
            )

    @property
    def session(self) -> requests.Session:
        if not self._session:
            self._session = self._create_session(
                self.api_key, self.include_user_agent, self.headers
            )
        return self._session

    @property
    def s3_client(self):
        if not self._s3_client:
            self._s3_client = boto3.client(
                "s3",
                config=Config(signature_version=UNSIGNED),  # type: ignore
            )
        return self._s3_client

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
    def _get_database_version(endpoint):
        """The Materials Project database is periodically updated and has a
        database version associated with it. When the database is updated,
        consolidated data (information about "a material") may and does
        change, while calculation data about a specific calculation task
        remains unchanged and available for querying via its task_id.

        The database version is set as a date in the format YYYY_MM_DD,
        where "_DD" may be optional. An additional numerical or `postN` suffix
        might be added if multiple releases happen on the same day.

        Returns: database version as a string
        """
        return requests.get(url=endpoint + "heartbeat").json()["db_version"]

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
        self,
        bucket: str,
        key: str,
        decoder: Callable | None = None,
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

    def _query_resource(
        self,
        criteria: dict | None = None,
        fields: list[str] | None = None,
        suburl: str | None = None,
        use_document_model: bool | None = None,
        parallel_param: str | None = None,
        num_chunks: int | None = None,
        chunk_size: int | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Query the endpoint for a Resource containing a list of documents
        and meta information about pagination and total document count.

        For the end-user, methods .search() and .count() are intended to be
        easier to use.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute
            parallel_param: parameter used to make parallel requests
            num_chunks: Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size: Number of data entries per chunk.
            timeout : Time in seconds to wait until a request timeout error is thrown

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """
        if use_document_model is None:
            use_document_model = self.use_document_model

        timeout = self.timeout if timeout is None else timeout

        criteria = {k: v for k, v in (criteria or {}).items() if v is not None}

        # Query s3 if no query is passed and all documents are asked for
        # TODO also skip fields set to same as their default
        no_query = not {field for field in criteria if field[0] != "_"}
        query_s3 = no_query and num_chunks is None

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
                if "/" not in self.suffix:
                    suffix = self.suffix
                elif self.suffix == "molecules/summary":
                    suffix = "molecules"
                else:
                    infix, suffix = self.suffix.split("/", 1)
                    suffix = infix if suffix == "core" else suffix
                    suffix = suffix.replace("_", "-")

                # Paginate over all entries in the bucket.
                # TODO: change when a subset of entries needed from DB
                if "tasks" in suffix:
                    bucket_suffix, prefix = "parsed", "tasks_atomate2"
                else:
                    bucket_suffix = "build"
                    prefix = f"collections/{self.db_version.replace('.', '-')}/{suffix}"

                bucket = f"materialsproject-{bucket_suffix}"
                paginator = self.s3_client.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

                keys = []
                for page in pages:
                    for obj in page.get("Contents", []):
                        key = obj.get("Key")
                        if key and "manifest" not in key:
                            keys.append(key)

                if len(keys) < 1:
                    return self._submit_requests(
                        url=url,
                        criteria=criteria,
                        use_document_model=use_document_model,
                        parallel_param=parallel_param,
                        num_chunks=num_chunks,
                        chunk_size=chunk_size,
                        timeout=timeout,
                    )

                if fields:
                    warnings.warn(
                        "Ignoring `fields` argument: All fields are always included when no query is provided."
                    )

                # Multithreaded function inputs
                s3_params_list = {
                    key: {
                        "bucket": bucket,
                        "key": key,
                    }
                    for key in keys
                }

                # Setup progress bar
                pbar_message = (  # type: ignore
                    f"Retrieving {self.document_model.__name__} documents"  # type: ignore
                    if self.document_model is not None
                    else "Retrieving documents"
                )
                num_docs_needed = int(self.count())
                pbar = (
                    tqdm(
                        desc=pbar_message,
                        total=num_docs_needed,
                    )
                    if not self.mute_progress_bars
                    else None
                )

                byte_data = self._multi_thread(
                    self._query_open_data,
                    list(s3_params_list.values()),
                    pbar,  # type: ignore
                )

                unzipped_data = []
                for docs, _, _ in byte_data:
                    unzipped_data.extend(docs)

                data = {"data": unzipped_data, "meta": {}}

                if self.use_document_model:
                    data["data"] = self._convert_to_model(data["data"])

                data["meta"]["total_doc"] = len(data["data"])
            else:
                data = self._submit_requests(
                    url=url,
                    criteria=criteria,
                    use_document_model=not query_s3 and use_document_model,
                    parallel_param=parallel_param,
                    num_chunks=num_chunks,
                    chunk_size=chunk_size,
                    timeout=timeout,
                )
            return data

        except RequestException as ex:
            raise MPRestError(str(ex))

    def _submit_requests(  # noqa
        self,
        url,
        criteria,
        use_document_model,
        chunk_size,
        parallel_param=None,
        num_chunks=None,
        timeout=None,
    ) -> dict:
        """Handle submitting requests. Parallel requests supported if possible.
        Parallelization will occur either over the largest list of supported
        query parameters used and/or over pagination.

        The number of threads is chosen by NUM_PARALLEL_REQUESTS in settings.

        Arguments:
            criteria: dictionary of criteria to filter down
            url: url used to make request
            use_document_model: if None, will defer to the self.use_document_model attribute
            parallel_param: parameter to parallelize requests with
            num_chunks: Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size: Number of data entries per chunk.
            timeout: Time in seconds to wait until a request timeout error is thrown

        Returns:
            Dictionary containing data and metadata
        """
        # Generate new sets of criteria dicts to be run in parallel
        # with new appropriate limit values. New limits obtained from
        # trying to evenly divide num_chunks by the total number of new
        # criteria dicts.
        if parallel_param is not None:
            # Determine slice size accounting for character maximum in HTTP URL
            # First get URl length without parallel param
            url_string = ""
            for key, value in criteria.items():
                if key != parallel_param:
                    parsed_val = quote(str(value))
                    url_string += f"{key}={parsed_val}&"

            bare_url_len = len(url_string)
            max_param_str_length = (
                MAPI_CLIENT_SETTINGS.MAX_HTTP_URL_LENGTH - bare_url_len  # type: ignore
            )

            # Next, check if default number of parallel requests works.
            # If not, make slice size the minimum number of param entries
            # contained in any substring of length max_param_str_length.
            param_length = len(criteria[parallel_param].split(","))
            slice_size = (
                int(param_length / MAPI_CLIENT_SETTINGS.NUM_PARALLEL_REQUESTS) or 1  # type: ignore
            )

            url_param_string = quote(criteria[parallel_param])

            parallel_param_str_chunks = [
                url_param_string[i : i + max_param_str_length]
                for i in range(0, len(url_param_string), max_param_str_length)
                if (i + max_param_str_length) <= len(url_param_string)
            ]

            if len(parallel_param_str_chunks) > 0:
                params_min_chunk = min(
                    parallel_param_str_chunks, key=lambda x: len(x.split("%2C"))
                )

                num_params_min_chunk = len(params_min_chunk.split("%2C"))

                if num_params_min_chunk < slice_size:
                    slice_size = num_params_min_chunk or 1

            new_param_values = [
                entry
                for entry in (
                    criteria[parallel_param].split(",")[i : (i + slice_size)]
                    for i in range(0, param_length, slice_size)
                )
                if entry != []
            ]

            # Get new limit values that sum to chunk_size
            num_new_params = len(new_param_values)
            q = int(chunk_size / num_new_params)  # quotient
            r = chunk_size % num_new_params  # remainder
            new_limits = []

            for _ in range(num_new_params):
                val = q + 1 if r > 0 else q if q > 0 else 1
                new_limits.append(val)
                r -= 1

            # Split list and generate multiple criteria
            new_criteria = [
                {
                    **{
                        key: criteria[key]
                        for key in criteria
                        if key not in [parallel_param, "_limit"]
                    },
                    parallel_param: ",".join(list_chunk),
                    "_limit": new_limits[list_num],
                }
                for list_num, list_chunk in enumerate(new_param_values)
            ]

        else:
            # Only parallelize over pagination parameters
            new_criteria = [criteria]
            new_limits = [chunk_size]

        total_num_docs = 0
        total_data: dict[str, list[Any]] = {"data": []}

        # Obtain first page of results and get pagination information.
        # Individual total document limits (subtotal) will potentially
        # be used for rebalancing should one new of the criteria
        # queries result in a smaller amount of docs compared to the
        # new limit value we assigned.
        subtotals = []
        remaining_docs_avail = {}

        initial_params_list = [
            {
                "url": url,
                "verify": True,
                "params": copy(crit),
                "use_document_model": use_document_model,
                "timeout": timeout,
            }
            for crit in new_criteria
        ]

        initial_data_tuples = self._multi_thread(
            self._submit_request_and_process, initial_params_list
        )

        for data, subtotal, crit_ind in initial_data_tuples:
            subtotals.append(subtotal)
            sub_diff = subtotal - new_limits[crit_ind]
            remaining_docs_avail[crit_ind] = sub_diff
            total_data["data"].extend(data["data"])

        last_data_entry = initial_data_tuples[-1][0]

        # Rebalance if some parallel queries produced too few results
        if len(remaining_docs_avail) > 1 and len(total_data["data"]) < chunk_size:
            remaining_docs_avail = dict(
                sorted(remaining_docs_avail.items(), key=lambda item: item[1])
            )

            # Redistribute missing docs from initial chunk among queries
            # which have head room with respect to remaining document number.
            fill_docs = 0
            rebalance_params = []
            for crit_ind, amount_avail in remaining_docs_avail.items():
                if amount_avail <= 0:
                    fill_docs += abs(amount_avail)
                    new_limits[crit_ind] = 0
                else:
                    crit = new_criteria[crit_ind]
                    crit["_skip"] = crit["_limit"]

                    if fill_docs == 0:
                        continue

                    if fill_docs >= amount_avail:
                        crit["_limit"] = amount_avail
                        new_limits[crit_ind] += amount_avail
                        fill_docs -= amount_avail

                    else:
                        crit["_limit"] = fill_docs
                        new_limits[crit_ind] += fill_docs
                        fill_docs = 0

                    rebalance_params.append(
                        {
                            "url": url,
                            "verify": True,
                            "params": copy(crit),
                            "use_document_model": use_document_model,
                            "timeout": timeout,
                        }
                    )

                    new_criteria[crit_ind]["_skip"] += crit["_limit"]
                    new_criteria[crit_ind]["_limit"] = chunk_size

            # Obtain missing initial data after rebalancing
            if len(rebalance_params) > 0:
                rebalance_data_tuples = self._multi_thread(
                    self._submit_request_and_process, rebalance_params
                )

                for data, _, _ in rebalance_data_tuples:
                    total_data["data"].extend(data["data"])

                last_data_entry = rebalance_data_tuples[-1][0]

        total_num_docs = sum(subtotals)

        if "meta" in last_data_entry:
            last_data_entry["meta"]["total_doc"] = total_num_docs
            total_data["meta"] = last_data_entry["meta"]

        # Get max number of response pages
        max_pages = (
            num_chunks if num_chunks is not None else ceil(total_num_docs / chunk_size)
        )

        # Get total number of docs needed
        num_docs_needed = min((max_pages * chunk_size), total_num_docs)

        # Setup progress bar
        pbar_message = (  # type: ignore
            f"Retrieving {self.document_model.__name__} documents"  # type: ignore
            if self.document_model is not None
            else "Retrieving documents"
        )
        pbar = (
            tqdm(
                desc=pbar_message,
                total=num_docs_needed,
            )
            if not self.mute_progress_bars
            else None
        )

        initial_data_length = len(total_data["data"])

        # If we have all the results in a single page, return directly
        if initial_data_length >= num_docs_needed or num_chunks == 1:
            new_total_data = copy(total_data)
            new_total_data["data"] = total_data["data"][:num_docs_needed]

            if pbar is not None:
                pbar.update(num_docs_needed)
                pbar.close()
            return new_total_data

        # otherwise, prepare to paginate in parallel
        if chunk_size is None:
            raise ValueError("A chunk size must be provided to enable pagination")

        if pbar is not None:
            pbar.update(initial_data_length)

        # Warning to select specific fields only for many results
        if criteria.get("_all_fields", False) and (total_num_docs / chunk_size > 10):
            warnings.warn(
                f"Use the 'fields' argument to select only fields of interest to speed "
                f"up data retrieval for large queries. "
                f"Choose from: {self.available_fields}"
            )

        # Get all pagination input params for parallel requests
        params_list = []
        doc_counter = 0

        for crit_num, crit in enumerate(new_criteria):
            remaining = remaining_docs_avail[crit_num]
            if "_skip" not in crit:
                crit["_skip"] = chunk_size if "_limit" not in crit else crit["_limit"]

            while remaining > 0:
                if doc_counter == (num_docs_needed - initial_data_length):
                    break

                if remaining < chunk_size:
                    crit["_limit"] = remaining
                    doc_counter += remaining
                else:
                    n = chunk_size - (doc_counter % chunk_size)
                    crit["_limit"] = n
                    doc_counter += n

                params_list.append(
                    {
                        "url": url,
                        "verify": True,
                        "params": {**crit, "_skip": crit["_skip"]},
                        "use_document_model": use_document_model,
                        "timeout": timeout,
                    }
                )

                crit["_skip"] += crit["_limit"]
                remaining -= crit["_limit"]

        # Submit requests and process data
        data_tuples = self._multi_thread(
            self._submit_request_and_process, params_list, pbar
        )

        for data, _, _ in data_tuples:
            total_data["data"].extend(data["data"])

        if data_tuples and "meta" in data_tuples[0][0]:
            total_data["meta"]["time_stamp"] = data_tuples[0][0]["meta"]["time_stamp"]

        if pbar is not None:
            pbar.close()

        return total_data

    def _multi_thread(
        self,
        func: Callable,
        params_list: list[dict],
        progress_bar: tqdm | None = None,
    ):
        """Handles setting up a threadpool and sending parallel requests.

        Arguments:
            func (Callable): Callable function to multi
            params_list (list): list of dictionaries containing url and params for each request
            progress_bar (tqdm): progress bar to update with progress

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
        headers = None
        if flask is not None and flask.has_request_context():
            headers = flask.request.headers

        try:
            response = self.session.get(
                url=url,
                verify=verify,
                params=params,
                timeout=timeout,
                headers=headers if headers else self.headers,
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
                data["data"] = self._convert_to_model(data["data"])

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

    def _convert_to_model(self, data: list[dict]):
        """Converts dictionary documents to instantiated MPDataDoc objects.

        Args:
            data (list[dict]): Raw dictionary data objects

        Returns:
            (list[MPDataDoc]): List of MPDataDoc objects

        """
        if len(data) > 0:
            data_model, set_fields, _ = self._generate_returned_model(data[0])

            data = [
                data_model(
                    **{
                        field: value
                        for field, value in dict(raw_doc).items()
                        if field in set_fields
                    }
                )
                for raw_doc in data
            ]

        return data

    def _generate_returned_model(
        self, doc: dict[str, Any]
    ) -> tuple[BaseModel, list[str], list[str]]:
        model_fields = self.document_model.model_fields
        set_fields = [k for k in doc if k in model_fields]
        unset_fields = [field for field in model_fields if field not in set_fields]

        # Update with locals() from external module if needed
        if any(
            isinstance(field_meta.annotation, ForwardRef)
            for field_meta in model_fields.values()
        ) or any(
            isinstance(typ, ForwardRef)
            for field_meta in model_fields.values()
            for typ in get_args(field_meta.annotation)
        ):
            vars(import_module(self.document_model.__module__))

        include_fields: dict[str, tuple[type, FieldInfo]] = {}
        for name in set_fields:
            field_copy = model_fields[name]._copy()
            if not field_copy.default_factory:
                # Fields with a default_factory cannot also have a default in pydantic>=2.12.3
                field_copy.default = None
            include_fields[name] = (
                Optional[model_fields[name].annotation],
                field_copy,
            )

        data_model = create_model(  # type: ignore
            "MPDataDoc",
            **include_fields,
            # TODO fields_not_requested is not the same as unset_fields
            # i.e. field could be requested but not available in the raw doc
            fields_not_requested=(list[str], unset_fields),
            __base__=_DictLikeAccess,
            __doc__=".".join(
                [
                    getattr(self.document_model, k, "")
                    for k in ("__module__", "__name__")
                ]
            ),
            __module__=self.document_model.__module__,
        )

        orig_rester_name = self.document_model.__name__

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

            s = f"\033[4m\033[1m{self.__class__.__name__}<{self.__class__.__base__.__name__}>\033[0;0m\033[0;0m\n{extra}\n\n\033[1mFields not requested:\033[0;0m\n{unset_fields}"  # noqa: E501
            return s

        def new_getattr(self, attr) -> str:
            if attr in self.fields_not_requested:
                raise AttributeError(
                    f"'{attr}' data is available but has not been requested in 'fields'."
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

        return data_model, set_fields, unset_fields

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
        **kwargs,
    ) -> list[BaseModel] | list[dict]:
        """A generic search method to retrieve documents matching specific parameters.

        Arguments:
            mute (bool): Whether to mute progress bars.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Set to False to only return specific fields of interest. This will
                significantly speed up data retrieval for large queries and help us by reducing
                load on the Materials Project servers. Set to True by default to reduce confusion,
                unless "fields" are set, in which case all_fields will be set to False.
            fields (List[str]): List of fields to project. When searching, it is better to only ask for
                the specific fields of interest to reduce the time taken to retrieve the documents. See
                 the available_fields property to see a list of fields to choose from.
            kwargs: Supported search terms, e.g. nelements_max=3 for the "materials" search API.
                Consult the specific API route for valid search terms.

        Returns:
            A list of documents.
        """
        # This method should be customized for each end point to give more user friendly,
        # documented kwargs.

        return self._get_all_documents(
            kwargs,
            all_fields=all_fields,
            fields=fields,
            chunk_size=chunk_size,
            num_chunks=num_chunks,
        )

    def get_data_by_id(
        self,
        document_id: str,
        fields: list[str] | None = None,
    ) -> BaseModel | dict:
        warnings.warn(
            "get_data_by_id is deprecated and will be removed soon. Please use the search method instead.",
            DeprecationWarning,
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

        docs = self._search(  # type: ignorech(  # type: ignorech(  # type: ignore
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
    ) -> list[BaseModel] | list[dict]:
        """Iterates over pages until all documents are retrieved. Displays
        progress using tqdm. This method is designed to give a common
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

        # Check if specific parameters are present that can be parallelized over
        list_entries = sorted(
            (
                (key, len(entry.split(",")))
                for key, entry in query_params.items()
                if isinstance(entry, str)
                and len(entry.split(",")) > 0
                and key not in MAPI_CLIENT_SETTINGS.QUERY_NO_PARALLEL  # type: ignore
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        chosen_param = list_entries[0][0] if len(list_entries) > 0 else None

        results = self._query_resource(
            query_params,
            fields=fields,
            parallel_param=chosen_param,
            chunk_size=chunk_size,
            num_chunks=num_chunks,
        )

        return results["data"]

    def count(self, criteria: dict | None = None) -> int | str:
        """Return a count of total documents.

        Args:
            criteria (dict | None): As in .search(). Defaults to None

        Returns:
            (int | str): Count of total results, or string indicating error
        """
        criteria = criteria or {}
        user_preferences = (
            self.use_document_model,
            self.mute_progress_bars,
        )
        self.use_document_model, self.mute_progress_bars = (
            False,
            True,
        )  # do not waste cycles decoding
        results = self._query_resource(criteria=criteria, num_chunks=1, chunk_size=1)
        cnt = results["meta"]["total_doc"]

        no_query = not {field for field in criteria if field[0] != "_"}
        if no_query and hasattr(self, "search"):
            allowed_params = inspect.getfullargspec(self.search).args
            if "deprecated" in allowed_params:
                criteria["deprecated"] = True
                results = self._query_resource(
                    criteria=criteria, num_chunks=1, chunk_size=1
                )
                cnt += results["meta"]["total_doc"]
                warnings.warn(
                    "Omitting a query also includes deprecated documents in the results. "
                    "Make sure to post-filter them out."
                )

        (
            self.use_document_model,
            self.mute_progress_bars,
        ) = user_preferences
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
                    include_user_agent=self._include_user_agent,
                    session=self.session,
                    use_document_model=self.use_document_model,
                    headers=self.headers,
                    mute_progress_bars=self.mute_progress_bars,
                )
            return self.sub_resters[v]

    def __dir__(self):
        return dir(self.__class__) + list(self._sub_resters)
