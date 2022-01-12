# coding: utf-8
"""
This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

import itertools
import json
import platform
import sys
import warnings
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from json import JSONDecodeError
from os import environ
from typing import Dict, Generic, List, Optional, TypeVar, Union
from urllib.parse import urljoin

import requests
from emmet.core.utils import jsanitize
from maggma.api.utils import api_sanitize
from monty.json import MontyDecoder
from mp_api.core.settings import MAPIClientSettings
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from tqdm.auto import tqdm
from urllib3.util.retry import Retry

try:
    from pymatgen.core import __version__ as pmg_version  # type: ignore
except ImportError:  # pragma: no cover
    # fallback to root-level import for older pymatgen versions
    from pymatgen import __version__ as pmg_version  # type: ignore

# TODO: think about how to migrate from PMG_MAPI_KEY
DEFAULT_API_KEY = environ.get("MP_API_KEY", None)
DEFAULT_ENDPOINT = environ.get("MP_API_ENDPOINT", "https://api.materialsproject.org/")

T = TypeVar("T")


class BaseRester(Generic[T]):
    """
    Base client class with core stubs
    """

    suffix: Optional[str] = None
    document_model: BaseModel = None  # type: ignore
    supports_versions: bool = False
    primary_key: str = "material_id"

    def __init__(
        self,
        api_key: Union[str, None] = DEFAULT_API_KEY,
        endpoint: str = DEFAULT_ENDPOINT,
        include_user_agent: bool = True,
        session: Optional[requests.Session] = None,
        debug: bool = False,
        monty_decode: bool = True,
        use_document_model: bool = True,
    ):
        """
        Args:
            api_key (str): A String API key for accessing the MaterialsProject
                REST interface. Please obtain your API key at
                https://www.materialsproject.org/dashboard. If this is None,
                the code will check if there is a "PMG_MAPI_KEY" setting.
                If so, it will use that environment variable. This makes
                easier for heavy users to simply add this environment variable to
                their setups and MPRester can then be called without any arguments.
            endpoint (str): Url of endpoint to access the MaterialsProject REST
                interface. Defaults to the standard Materials Project REST
                address at "https://api.materialsproject.org", but
                can be changed to other urls implementing a similar interface.
            include_user_agent (bool): If True, will include a user agent with the
                HTTP request including information on pymatgen and system version
                making the API request. This helps MP support pymatgen users, and
                is similar to what most web browsers send with each page request.
                Set to False to disable the user agent.
            session: requests Session object with which to connect to the API, for
                advanced usage only.
            debug: if True, print the URL for every request
            monty_decode: Decode the data using monty into python objects
            use_document_model: If False, skip the creating the document model and return data
                as a dictionary. This can be simpler to work with but bypasses data validation
                and will not give auto-complete for available fields.
        """

        self.api_key = api_key
        self.base_endpoint = endpoint
        self.endpoint = endpoint
        self.debug = debug
        self.include_user_agent = include_user_agent
        self.monty_decode = monty_decode
        self.use_document_model = use_document_model

        if self.suffix:
            self.endpoint = urljoin(self.endpoint, self.suffix)
        if not self.endpoint.endswith("/"):
            self.endpoint += "/"

        if session:
            self._session = session
        else:
            self._session = None  # type: ignore

        self.document_model = (
            api_sanitize(self.document_model)  # type: ignore
            if self.document_model is not None
            else None
        )

    @property
    def session(self) -> requests.Session:
        if not self._session:
            self._session = self._create_session(self.api_key, self.include_user_agent)
        return self._session

    @staticmethod
    def _create_session(api_key, include_user_agent):
        session = requests.Session()
        session.trust_env = False
        session.headers = {"x-api-key": api_key}
        if include_user_agent:
            pymatgen_info = "pymatgen/" + pmg_version
            python_info = "Python/{}.{}.{}".format(
                sys.version_info.major, sys.version_info.minor, sys.version_info.micro
            )
            platform_info = "{}/{}".format(platform.system(), platform.release())
            session.headers["user-agent"] = "{} ({} {})".format(
                pymatgen_info, python_info, platform_info
            )

        max_retry_num = MAPIClientSettings().MAX_RETRIES
        retry = Retry(
            total=max_retry_num,
            read=max_retry_num,
            connect=max_retry_num,
            respect_retry_after_header=True,
            status_forcelist=[429],  # rate limiting
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def __enter__(self):  # pragma: no cover
        """
        Support for "with" context.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        """
        Support for "with" context.
        """
        if self.session is not None:
            self.session.close()
        self._session = None

    def _post_resource(
        self,
        body: Dict = None,
        params: Optional[Dict] = None,
        suburl: Optional[str] = None,
        use_document_model: Optional[bool] = None,
    ) -> Dict:
        """
        Post data to the endpoint for a Resource.

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

                if self.monty_decode:
                    data = json.loads(response.text, cls=MontyDecoder)
                else:
                    data = json.loads(response.text)

                if self.document_model and use_document_model:
                    if isinstance(data["data"], dict):
                        data["data"] = self.document_model.parse_obj(data["data"])  # type: ignore
                    elif isinstance(data["data"], list):
                        data["data"] = [self.document_model.parse_obj(d) for d in data["data"]]  # type: ignore

                return data

            else:
                try:
                    data = json.loads(response.text)["detail"]
                except (JSONDecodeError, KeyError):
                    data = "Response {}".format(response.text)
                if isinstance(data, str):
                    message = data
                else:
                    try:
                        message = ", ".join(
                            "{} - {}".format(entry["loc"][1], entry["msg"])
                            for entry in data
                        )
                    except (KeyError, IndexError):
                        message = str(data)

                raise MPRestError(
                    f"REST post query returned with error status code {response.status_code} "
                    f"on URL {response.url} with message:\n{message}"
                )

        except RequestException as ex:

            raise MPRestError(str(ex))

    def _query_resource(
        self,
        criteria: Optional[Dict] = None,
        fields: Optional[List[str]] = None,
        suburl: Optional[str] = None,
        use_document_model: Optional[bool] = None,
        parallel_param: Optional[str] = None,
        num_chunks: Optional[int] = None,
        chunk_size: Optional[int] = None,
    ) -> Dict:
        """
        Query the endpoint for a Resource containing a list of documents
        and meta information about pagination and total document count.

        For the end-user, methods .query() and .count() are intended to be
        easier to use.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute
            parallel_param: parameter used to make parallel requests
            num_chunks: Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size: Number of data entries per chunk.

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """

        if use_document_model is None:
            use_document_model = self.use_document_model

        if criteria:
            criteria = {k: v for k, v in criteria.items() if v is not None}
        else:
            criteria = {}

        if fields:
            if isinstance(fields, str):
                fields = [fields]
            criteria["fields"] = ",".join(fields)

        try:
            url = self.endpoint
            if suburl:
                url = urljoin(self.endpoint, suburl)
                if not url.endswith("/"):
                    url += "/"

            data = self._submit_requests(
                url=url,
                criteria=criteria,
                use_document_model=use_document_model,
                parallel_param=parallel_param,
                num_chunks=num_chunks,
                chunk_size=chunk_size,
            )

            return data

        except RequestException as ex:

            raise MPRestError(str(ex))

    def _submit_requests(
        self,
        url,
        criteria,
        use_document_model,
        parallel_param=None,
        num_chunks=None,
        chunk_size=None,
    ):
        """
        Handle submitting requests. Parallel requests supported if possible.
        Parallelization will occur either over the largest list of supported
        query parameters used, or over pagination.

        By default, 8 threads are used for concurrent requests.

        Arguments:
            criteria: dictionary of criteria to filter down
            url: url used to make request
            use_document_model: if None, will defer to the self.use_document_model attribute
            parallel_param: parameter to parallelize requests with

        Returns:
            Dictionary containing data and metadata
        """

        # Handle parallelization over specific non pagination related list parameter
        if parallel_param is not None:
            param_length = len(criteria[parallel_param])
            slice_size = (
                int(param_length / MAPIClientSettings().NUM_PARALLEL_REQUESTS) or 1
            )

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
            q = int(chunk_size / num_new_params)
            r = chunk_size % num_new_params
            new_limits = []

            for _ in range(num_new_params):
                val = q + 1 if r > 0 else q
                new_limits.append(val)
                r -= 1

            # Split list and generate multiple criteria
            new_criteria = [
                {
                    **{
                        key: criteria[key]
                        for key in criteria
                        if key not in [parallel_param, "limit"]
                    },
                    parallel_param: ",".join(list_chunk),
                    "limit": new_limits[list_num],
                }
                for list_num, list_chunk in enumerate(new_param_values)
            ]

        else:
            # Only parallelize over pagination parameters
            new_criteria = [criteria]
            new_limits = [chunk_size]

        total_num_docs = 0
        total_data = {"data": []}

        # Obtain first page of results and get pagination information
        for crit in new_criteria:

            # Check how much pagination is needed
            response = self.session.get(url, verify=True, params=crit)

            data, subtotal = self._handle_response(response, use_document_model)
            total_num_docs += subtotal

            total_data["data"].extend(data["data"])

            crit["limit"] = chunk_size

        if "meta" in data:
            data["meta"]["total_doc"] = total_num_docs
            total_data["meta"] = data["meta"]

        # If we have all the results in a single page, return directly
        if len(total_data["data"]) == total_num_docs or num_chunks == 1:
            return total_data

        if chunk_size is None:
            raise ValueError("A chunk size must be provided to enable pagination")

        # otherwise prepare to paginate in parallel
        max_pages = (
            num_chunks
            if num_chunks is not None
            else (int(total_num_docs / chunk_size) + 1)
        )

        if num_chunks is not None:
            total_num_docs = min(len(total_data["data"]) * num_chunks, total_num_docs)

        # Setup progress bar
        t = tqdm(
            desc=f"Retrieving {self.document_model.__name__} documents",  # type: ignore
            total=total_num_docs,
        )
        t.update(len(total_data["data"]))

        # Warning to select specific fields only for many results
        if criteria.get("all_fields", False) and (total_num_docs / chunk_size > 10):
            warnings.warn(
                f"Use the 'fields' argument to select only fields of interest to speed "
                f"up data retrieval for large queries. "
                f"Choose from: {self.available_fields}"
            )

        # Get all get input params for parallel requests
        params_list = []
        exit = False

        for page_num in range(0, max_pages - 1):
            for crit_num, crit in enumerate(new_criteria):

                if (
                    num_chunks is not None
                    and (((page_num + 1) * (crit_num + 1))) == num_chunks
                ):
                    exit = True
                    break

                skip = new_limits[crit_num] + int(page_num * chunk_size)

                params_list.append(
                    {"url": url, "verify": True, "params": {**crit, "skip": skip}}
                )

            if exit:
                break

        params_gen = iter(
            params_list
        )  # Iter necessary for islice to keep track of what has been accessed

        with ThreadPoolExecutor(
            max_workers=MAPIClientSettings().NUM_PARALLEL_REQUESTS
        ) as executor:

            # Get list of initial futures defined by max number of parallel requests
            futures = {
                executor.submit(self.session.get, **params)
                for params in itertools.islice(
                    params_gen, MAPIClientSettings().NUM_PARALLEL_REQUESTS
                )
            }

            while futures:
                # Wait for at least one future to complete and process finished
                finished, futures = wait(futures, return_when=FIRST_COMPLETED)

                for future in finished:
                    response = future.result()
                    data, _ = self._handle_response(response, use_document_model)
                    t.update(len(data["data"]))
                    total_data["data"].extend(data["data"])

                # Populate more futures to replace finished
                for params in itertools.islice(params_gen, len(finished)):
                    futures.add(executor.submit(self.session.get, **params))

        if "meta" in data:
            total_data["meta"]["time_stamp"] = data["meta"]["time_stamp"]

        return total_data

    def _handle_response(self, response, use_document_model):
        """
        Handles resolved requests.

        Arguments:
            response: response from request
            use_document_model: if None, will defer to the self.use_document_model attribute

        Returns:
            Tuple with data and total number of docs in matching the query in the database.
        """

        if response.status_code == 200:

            if self.monty_decode:
                data = json.loads(response.text, cls=MontyDecoder)
            else:
                data = json.loads(response.text)

            # other sub-urls may use different document models
            # the client does not handle this in a particularly smart way currently
            if self.document_model and use_document_model:
                data["data"] = [self.document_model.parse_obj(d) for d in data["data"]]  # type: ignore

            meta_total_doc_num = data.get("meta", {}).get("total_doc", 1)

            return data, meta_total_doc_num

        else:
            try:
                data = json.loads(response.text)["detail"]
            except (JSONDecodeError, KeyError):
                data = "Response {}".format(response.text)
            if isinstance(data, str):
                message = data
            else:
                try:
                    message = ", ".join(
                        "{} - {}".format(entry["loc"][1], entry["msg"])
                        for entry in data
                    )
                except (KeyError, IndexError):
                    message = str(data)

            raise MPRestError(
                f"REST query returned with error status code {response.status_code} "
                f"on URL {response.url} with message:\n{message}"
            )

    def _query_resource_data(
        self,
        criteria: Optional[Dict] = None,
        fields: Optional[List[str]] = None,
        suburl: Optional[str] = None,
        use_document_model: Optional[bool] = None,
    ) -> Union[List[T], List[Dict]]:
        """
        Query the endpoint for a list of documents without associated meta information. Only
        returns a single page of results.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            suburl: make a request to a specified sub-url
            use_document_model: if None, will defer to the self.use_document_model attribute

        Returns:
            A list of documents
        """

        return self._query_resource(  # type: ignore
            criteria=criteria,
            fields=fields,
            suburl=suburl,
            use_document_model=use_document_model,
            num_chunks=1,
        ).get("data")

    def get_data_by_id(
        self, document_id: str, fields: Optional[List[str]] = None,
    ) -> T:
        """
        Query the endpoint for a single document.

        Arguments:
            document_id: the unique key for this kind of document, typically a task_id
            fields: list of fields to return, by default will return all fields

        Returns:
            A single document.
        """

        if document_id is None:
            raise ValueError(
                "Please supply a specific id. You can use the query method to find "
                "ids of interest."
            )

        if fields is None:
            criteria = {"all_fields": True, "limit": 1}  # type: dict
        else:
            criteria = {"limit": 1}

        if isinstance(fields, str):  # pragma: no cover
            fields = (fields,)

        results = []  # type: List

        try:
            results = self._query_resource_data(
                criteria=criteria, fields=fields, suburl=document_id,  # type: ignore
            )
        except MPRestError:

            if self.primary_key == "material_id":
                # see if the material_id has changed, perhaps a task_id was supplied
                # this should likely be re-thought
                from mp_api.matproj import MPRester

                with MPRester(api_key=self.api_key, endpoint=self.base_endpoint) as mpr:
                    new_document_id = mpr.get_materials_id_from_task_id(document_id)

                if new_document_id is not None:
                    warnings.warn(
                        f"Document primary key has changed from {document_id} to {new_document_id}, "
                        f"returning data for {new_document_id} in {self.suffix} route.    "
                    )
                    document_id = new_document_id

                    results = self._query_resource_data(
                        criteria=criteria, fields=fields, suburl=document_id,  # type: ignore
                    )

        if not results:
            raise MPRestError(f"No result for record {document_id}.")
        elif len(results) > 1:  # pragma: no cover
            raise ValueError(
                f"Multiple records for {document_id}, this shouldn't happen. Please report as a bug."
            )
        else:
            return results[0]

    def search(
        self,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
        **kwargs,
    ) -> Union[List[T], List[Dict]]:
        """
        A generic search method to retrieve documents matching specific parameters.

        Arguments:
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

    def _get_all_documents(
        self,
        query_params,
        all_fields=True,
        fields=None,
        chunk_size=1000,
        num_chunks=None,
    ) -> Union[List[T], List[Dict]]:
        """
        Iterates over pages until all documents are retrieved. Displays
        progress using tqdm. This method is designed to give a common
        implementation for the search_* methods on various endpoints. See
        materials endpoint for an example of this in use.
        """

        if all_fields and not fields:
            query_params["all_fields"] = True

        query_params["limit"] = chunk_size

        # Check if specific parameters are present that can be parallelized over
        list_entries = sorted(
            [
                (key, len(entry.split(",")))
                for key, entry in query_params.items()
                if isinstance(entry, str)
                and len(entry.split(",")) > 0
                and key not in MAPIClientSettings().QUERY_NO_PARALLEL
            ],
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

    def count(self, criteria: Optional[Dict] = None) -> Union[int, str]:
        """
        Return a count of total documents.
        :param criteria: As in .query()
        :return:
        """
        try:
            criteria = criteria or {}
            criteria[
                "limit"
            ] = 1  # we just want the meta information, only ask for single document
            user_preferences = self.monty_decode, self.use_document_model
            self.monty_decode, self.use_document_model = (
                False,
                False,
            )  # do not waste cycles decoding
            results = self._query_resource(criteria=criteria)
            self.monty_decode, self.use_document_model = user_preferences
            return results["meta"]["total_doc"]
        except Exception:  # pragma: no cover
            return "Problem getting count"

    @property
    def available_fields(self) -> List[str]:
        if self.document_model is None:
            return ["Unknown fields."]
        return list(self.document_model.schema()["properties"].keys())  # type: ignore

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} {self.endpoint}>"

    def __str__(self):  # pragma: no cover
        if self.document_model is None:
            return self.__repr__()
        return (
            f"{self.__class__.__name__} connected to {self.endpoint}\n\n"
            f"Available fields: {', '.join(self.available_fields)}\n\n"
        )


class MPRestError(Exception):
    """
    Raised when the query has problems, e.g., bad query format.
    """
