"""This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

from __future__ import annotations

import inspect
import os
import platform
import sys
import warnings
from copy import copy
from functools import cache
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from json import JSONDecodeError
from math import ceil
from typing import TYPE_CHECKING, ForwardRef, Optional, get_args
from urllib.parse import urljoin

import requests
from emmet.core.utils import jsanitize
from pydantic import BaseModel, create_model
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from smart_open import open
from tqdm.auto import tqdm
from urllib3.util.retry import Retry

from mp_api.client.core.exceptions import MPRestError
from mp_api.client.core.settings import MAPIClientSettings
from mp_api.client.core.utils import load_json, validate_ids

try:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
except ImportError:
    boto3 = None

try:
    import flask
except ImportError:
    flask = None

if TYPE_CHECKING:
    from typing import Any, Callable

    from pydantic.fields import FieldInfo

try:
    __version__ = version("mp_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION")


SETTINGS = MAPIClientSettings()  # type: ignore


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
    supports_versions: bool = False
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
        mute_progress_bars: bool = SETTINGS.MUTE_PROGRESS_BARS,
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
        # TODO: think about how to migrate from PMG_MAPI_KEY
        self.api_key = api_key or os.getenv("MP_API_KEY")
        self.base_endpoint = self.endpoint = endpoint or os.getenv(
            "MP_API_ENDPOINT", "https://api.materialsproject.org/"
        )
        self.debug = debug
        self.include_user_agent = include_user_agent
        self.use_document_model = use_document_model
        self.timeout = timeout
        self.headers = headers or {}
        self.mute_progress_bars = mute_progress_bars
        self.db_version = BaseRester._get_database_version(self.endpoint)

        if self.suffix:
            self.endpoint = urljoin(self.endpoint, self.suffix)
        if not self.endpoint.endswith("/"):
            self.endpoint += "/"

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
        if boto3 is None:
            raise MPRestError(
                "boto3 not installed. To query charge density, "
                "band structure, or density of states data first "
                "install with: 'pip install boto3'"
            )

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

        settings = MAPIClientSettings()  # type: ignore
        max_retry_num = settings.MAX_RETRIES
        retry = Retry(
            total=max_retry_num,
            read=max_retry_num,
            connect=max_retry_num,
            respect_retry_after_header=True,
            status_forcelist=[429, 504, 502],  # rate limiting
            backoff_factor=settings.BACKOFF_FACTOR,
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
            url = self.endpoint
            if suburl:
                url = urljoin(self.endpoint, suburl)
                if not url.endswith("/"):
                    url += "/"
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
            url = self.endpoint
            if suburl:
                url = urljoin(self.endpoint, suburl)
                if not url.endswith("/"):
                    url += "/"
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
        decoder = decoder or load_json

        file = open(
            f"s3://{bucket}/{key}",
            encoding="utf-8",
            transport_params={"client": self.s3_client},
        )

        if "jsonl" in key:
            decoded_data = [decoder(jline) for jline in file.read().splitlines()]
        else:
            decoded_data = decoder(file.read())
            if not isinstance(decoded_data, list):
                decoded_data = [decoded_data]

        return decoded_data, len(decoded_data)  # type: ignore

    def _query_resource(
        self,
        criteria: dict | None = None,
        fields: list[str] | None = None,
        suburl: str | None = None,
        use_document_model: bool | None = None,
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
            url = self.endpoint
            if suburl:
                url = urljoin(self.endpoint, suburl)
                if not url.endswith("/"):
                    url += "/"

            if query_s3:
                db_version = self.db_version.replace(".", "-")
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
                    prefix = f"collections/{db_version}/{suffix}"

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
        num_chunks=None,
        timeout=None,
    ) -> dict:
        """Handle submitting requests sequentially with pagination.

        If criteria contains comma-separated parameters (except those that are naturally comma-separated),
        split them into multiple sequential requests and combine results.

        Arguments:
            criteria: dictionary of criteria to filter down
            url: url used to make request
            use_document_model: if None, will defer to the self.use_document_model attribute
            num_chunks: Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size: Number of data entries per chunk.
            timeout: Time in seconds to wait until a request timeout error is thrown

        Returns:
            Dictionary containing data and metadata
        """
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

        # Check if we need to split any comma-separated parameters
        split_param = None
        split_values = None
        total_num_docs = 0  # Initialize before try/else blocks

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
        if split_param and split_values and len(split_values) > 1:
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

                # Check if we got 0 results - some parameters are silently ignored by the API
                # when passed as comma-separated values, so we need to split them anyway
                if total_num_docs == 0 and len(split_values) > 1:
                    # Treat this the same as a 422 error - split into batches
                    raise MPRestError(
                        "Got 0 results for comma-separated parameter, will try splitting"
                    )

                # If successful, continue with normal pagination
                total_data = {"data": []}  # type: dict
                total_data["data"].extend(data["data"])

                if "meta" in data:
                    total_data["meta"] = data["meta"]

                # Continue with pagination if needed (handled below)

            except MPRestError as e:
                # If we get 422 or 414 error, or 0 results for comma-separated params, split into batches
                if "422" in str(e) or "414" in str(e) or "Got 0 results" in str(e):
                    total_data = {"data": []}  # type: dict
                    total_num_docs = 0

                    # Batch the split values to reduce number of requests
                    # Use batches of up to 100 values to balance URL length and request count
                    batch_size = min(100, max(1, len(split_values) // 10))

                    # Setup progress bar for split parameter requests
                    num_batches = ceil(len(split_values) / batch_size)
                    pbar_message = f"Retrieving {len(split_values)} {split_param} values in {num_batches} batches"
                    pbar = (
                        tqdm(
                            desc=pbar_message,
                            total=num_batches,
                        )
                        if not self.mute_progress_bars
                        else None
                    )

                    for i in range(0, len(split_values), batch_size):
                        batch = split_values[i : i + batch_size]
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
                        )

                        total_data["data"].extend(result["data"])
                        if "meta" in result:
                            total_data["meta"] = result["meta"]
                            total_num_docs += result["meta"].get("total_doc", 0)

                        if pbar is not None:
                            pbar.update(1)

                    if pbar is not None:
                        pbar.close()

                    # Update total_doc if we have meta
                    if "meta" in total_data:
                        total_data["meta"]["total_doc"] = total_num_docs

                    return total_data
                else:
                    # Re-raise other errors
                    raise
        else:
            # No splitting needed - get first page
            total_data = {"data": []}  # type: dict
            initial_criteria = copy(criteria)
            data, total_num_docs = self._submit_request_and_process(
                url=url,
                verify=True,
                params=initial_criteria,
                use_document_model=use_document_model,
                timeout=timeout,
            )

            total_data["data"].extend(data["data"])

            if "meta" in data:
                total_data["meta"] = data["meta"]

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

        if pbar is not None:
            pbar.update(initial_data_length)

        # If we have all the results in a single page, return directly
        if initial_data_length >= num_docs_needed or num_chunks == 1:
            new_total_data = copy(total_data)
            new_total_data["data"] = total_data["data"][:num_docs_needed]

            if pbar is not None:
                pbar.close()
            return new_total_data

        # otherwise, paginate sequentially
        if chunk_size is None:
            raise ValueError("A chunk size must be provided to enable pagination")

        # Warning to select specific fields only for many results
        if criteria.get("_all_fields", False) and (total_num_docs / chunk_size > 10):
            warnings.warn(
                f"Use the 'fields' argument to select only fields of interest to speed "
                f"up data retrieval for large queries. "
                f"Choose from: {self.available_fields}"
            )

        # Paginate through remaining results
        skip = chunk_size if "_limit" not in criteria else criteria["_limit"]
        remaining_docs = total_num_docs - initial_data_length

        while len(total_data["data"]) < num_docs_needed and remaining_docs > 0:
            page_criteria = copy(criteria)
            page_criteria["_skip"] = skip

            # Determine limit for this request
            docs_still_needed = num_docs_needed - len(total_data["data"])
            page_criteria["_limit"] = min(chunk_size, docs_still_needed, remaining_docs)

            data, _ = self._submit_request_and_process(
                url=url,
                verify=True,
                params=page_criteria,
                use_document_model=use_document_model,
                timeout=timeout,
            )

            total_data["data"].extend(data["data"])

            if pbar is not None:
                pbar.update(len(data["data"]))

            skip += page_criteria["_limit"]
            remaining_docs -= len(data["data"])

            # Break if we didn't get any data (shouldn't happen, but safety check)
            if len(data["data"]) == 0:
                break

        if pbar is not None:
            pbar.close()

        return total_data

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

        results = self._query_resource(
            query_params,
            fields=fields,
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
