# coding: utf-8
"""
This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

import json
import platform
import sys
from json import JSONDecodeError
from typing import Dict, Optional, List, Union
from urllib.parse import urljoin
from os import environ
import warnings

import requests
from monty.json import MontyDecoder
from requests.exceptions import RequestException
from pydantic import BaseModel
from tqdm import tqdm

from emmet.core.utils import jsanitize
from maggma.api.utils import api_sanitize

from mp_api.core.ratelimit import check_limit

try:
    from pymatgen.core import __version__ as pmg_version  # type: ignore
except ImportError:  # pragma: no cover
    # fallback to root-level import for older pymatgen versions
    from pymatgen import __version__ as pmg_version  # type: ignore

# TODO: think about how to migrate from PMG_MAPI_KEY
DEFAULT_API_KEY = environ.get("MP_API_KEY", None)
DEFAULT_ENDPOINT = environ.get("MP_API_ENDPOINT", "https://api.materialsproject.org/")


class BaseRester:
    """
    Base client class with core stubs
    """

    suffix: Optional[str] = None
    document_model: Optional[BaseModel] = None
    supports_versions: bool = False
    primary_key: str = "material_id"

    def __init__(
        self,
        api_key=DEFAULT_API_KEY,
        endpoint=DEFAULT_ENDPOINT,
        include_user_agent=True,
        session=None,
        debug=False,
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
        """

        self.api_key = api_key
        self.base_endpoint = endpoint
        self.endpoint = endpoint
        self.debug = debug

        if self.suffix:
            self.endpoint = urljoin(self.endpoint, self.suffix)
        if not self.endpoint.endswith("/"):
            self.endpoint += "/"

        if session:
            self.session = session
        else:
            self.session = self._create_session(api_key, include_user_agent)

        self.document_model = (
            api_sanitize(self.document_model)
            if self.document_model is not None
            else None
        )

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
        self.session.close()

    def _post_resource(
        self,
        body: Dict = None,
        params: Optional[Dict] = None,
        monty_decode: bool = True,
        suburl: Optional[str] = None,
        use_document_model: Optional[bool] = True,
    ):
        """
        Post data to the endpoint for a Resource.

        Arguments:
            body: body json to send in post request
            params: extra params to send in post request
            monty_decode: Decode the data using monty into python objects
            suburl: make a request to a specified sub-url
            use_document_model: whether to use the core document model for data reconstruction

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """

        check_limit()

        payload = jsanitize(body)

        try:
            url = self.endpoint
            if suburl:
                url = urljoin(self.endpoint, suburl)
                if not url.endswith("/"):
                    url += "/"
            response = self.session.post(url, json=payload, verify=True, params=params)

            if response.status_code == 200:

                if monty_decode:
                    data = json.loads(response.text, cls=MontyDecoder)
                else:
                    data = json.loads(response.text)

                if self.document_model and use_document_model:
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
        monty_decode: bool = True,
        suburl: Optional[str] = None,
        use_document_model: Optional[bool] = True,
    ):
        """
        Query the endpoint for a Resource containing a list of documents
        and meta information about pagination and total document count.

        For the end-user, methods .query() and .count() are intended to be
        easier to use.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            monty_decode: Decode the data using monty into python objects
            suburl: make a request to a specified sub-url
            use_document_model: whether to use the core document model for data reconstruction

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """

        check_limit()

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
            response = self.session.get(url, verify=True, params=criteria)

            if response.status_code == 200:

                if monty_decode:
                    data = json.loads(response.text, cls=MontyDecoder)
                else:
                    data = json.loads(response.text)

                if self.document_model and use_document_model:
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
                    f"REST query returned with error status code {response.status_code} "
                    f"on URL {response.url} with message:\n{message}"
                )

        except RequestException as ex:

            raise MPRestError(str(ex))

    def query(
        self,
        criteria: Optional[Dict] = None,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
        suburl: Optional[str] = None,
    ):
        """
        Query the endpoint for a list of documents.

        Arguments:
            criteria: dictionary of criteria to filter down
            fields: list of fields to return
            monty_decode: Decode the data using monty into python objects
            suburl: make a request to a specified sub-url

        Returns:
            A list of documents
        """
        return self._query_resource(
            criteria=criteria, fields=fields, monty_decode=monty_decode, suburl=suburl,
        ).get("data")

    def get_document_by_id(
        self,
        document_id: str,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
    ):
        """
        Query the endpoint for a single document.

        Arguments:
            document_id: the unique key for this kind of document, typically a task_id
            fields: list of fields to return, by default will return all fields
            monty_decode: Decode the data using monty into python objects

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

        results = []

        try:
            results = self.query(
                criteria=criteria,
                fields=fields,
                monty_decode=monty_decode,
                suburl=document_id,
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

                    results = self.query(
                        criteria=criteria,
                        fields=fields,
                        monty_decode=monty_decode,
                        suburl=document_id,
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
    ):
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
    ):
        """
        Iterates over pages until all documents are retrieved. Displays
        progress using tqdm. This method is designed to give a common
        implementation for the search_* methods on various endpoints. See
        materials endpoint for an example of this in use.
        """

        if all_fields and not fields:
            query_params["all_fields"] = True

        query_params["limit"] = chunk_size

        results = self._query_resource(query_params, fields=fields)

        # if we have all the results in a single page, return directly
        if len(results["data"]) == results["meta"]["total_doc"]:
            return results["data"]

        # otherwise prepare to iterate over all pages
        all_results = results["data"]
        count = 1

        # progress bar
        total_docs = results["meta"]["total_doc"]
        t = tqdm(
            desc=f"Retrieving {self.document_model.__name__} documents",
            total=total_docs,
        )
        t.update(len(all_results))

        # warn to select specific fields only for many results
        if (not fields) and (total_docs / chunk_size > 10):
            warnings.warn(
                f"Use the 'fields' argument to select only fields of interest to speed "
                f"up data retrieval for large queries. "
                f"Choose from: {self.available_fields}"
            )

        while True:
            query_params["skip"] = count * chunk_size
            results = self._query_resource(query_params, fields=fields)

            t.update(len(results["data"]))

            if not any(results["data"]) or (
                num_chunks is not None and count == num_chunks
            ):
                break

            count += 1
            all_results += results["data"]

        return all_results

    def query_by_task_id(self, *args, **kwargs):  # pragma: no cover
        print(
            "query_by_task_id has been renamed to get_document_by_id to be more general"
        )
        return self.get_document_by_id(*args, **kwargs)

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
            results = self._query_resource(
                criteria=criteria, monty_decode=False
            )  # do not waste cycles Monty decoding
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
