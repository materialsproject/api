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
from pymatgen import __version__ as pmg_version  # type: ignore
from requests.exceptions import RequestException
from pydantic import BaseModel

# TODO: think about how to migrate from PMG_MAPI_KEY
DEFAULT_API_KEY = environ.get("MP_API_KEY", None)
DEFAULT_ENDPOINT = environ.get("MP_API_ENDPOINT", "https://api.materialsproject.org/")


class BaseRester:
    """
    Base client class with core stubs
    """

    suffix: Optional[str] = None
    document_model: Optional[BaseModel] = None

    def __init__(
        self,
        api_key=DEFAULT_API_KEY,
        endpoint=DEFAULT_ENDPOINT,
        debug=True,
        version=None,
        include_user_agent=True,
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
            version (Optional[str]): Specify the database snapshot to query.
            include_user_agent (bool): If True, will include a user agent with the
                HTTP request including information on pymatgen and system version
                making the API request. This helps MP support pymatgen users, and
                is similar to what most web browsers send with each page request.
                Set to False to disable the user agent.
        """

        self.api_key = api_key
        self.endpoint = endpoint
        self.debug = debug
        self.version = version

        if self.suffix:
            self.endpoint = urljoin(self.endpoint, self.suffix)
        self.endpoint += "/"

        self.session = requests.Session()
        self.session.headers = {"x-api-key": self.api_key}
        if include_user_agent:
            pymatgen_info = "pymatgen/" + pmg_version
            python_info = "Python/{}.{}.{}".format(
                sys.version_info.major, sys.version_info.minor, sys.version_info.micro
            )
            platform_info = "{}/{}".format(platform.system(), platform.release())
            self.session.headers["user-agent"] = "{} ({} {})".format(
                pymatgen_info, python_info, platform_info
            )

    def __enter__(self):
        """
        Support for "with" context.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Support for "with" context.
        """
        self.session.close()

    def _make_request(self, sub_url, monty_decode: bool = True):
        """
        Helper function to make requests

        Arguments:
            sub_url: the URL to request
            monty_decode: Decode the data using monty into python objects
        """
        print("_make_request is going away", sub_url)

        url = self.endpoint + sub_url
        if self.debug:
            print(f"URL: {url}")

        try:
            response = self.session.get(url, verify=True)
            if response.status_code == 200:
                if monty_decode:
                    data = json.loads(response.text, cls=MontyDecoder)
                else:
                    data = json.loads(response.text)

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

    def _query_resource(
        self,
        criteria: Optional[Dict] = None,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
        suburl: Optional[str] = None,
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

        Returns:
            A Resource, a dict with two keys, "data" containing a list of documents, and
            "meta" containing meta information, e.g. total number of documents
            available.
        """

        if criteria:
            criteria = {k: v for k, v in criteria.items() if v is not None}
        else:
            criteria = {}

        if fields:
            criteria["fields"] = ",".join(fields)

        try:
            url = self.endpoint
            if suburl:
                url = urljoin(self.endpoint, suburl)
            response = self.session.get(url, verify=True, params=criteria)

            if response.status_code == 200:

                if monty_decode:
                    data = json.loads(response.text, cls=MontyDecoder)
                else:
                    data = json.loads(response.text)

                if self.document_model:
                    data["data"] = [self.document_model.construct(**d) for d in data["data"]]  # type: ignore

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
            criteria=criteria, fields=fields, monty_decode=monty_decode, suburl=suburl
        ).get("data")

    def query_by_task_id(
        self,
        task_id,
        fields: Optional[List[str]] = None,
        monty_decode: bool = True,
        version: Optional[str] = None,
    ):
        """
        Query the endpoint for a single document.

        Arguments:
            task_id: a task_id key
            fields: list of fields to return
            monty_decode: Decode the data using monty into python objects

        Returns:
            A single document.
        """

        if fields is None:
            criteria = {"all_fields": True, "limit": 1}
        else:
            criteria = {"limit": 1}

        if version:
            criteria["version"] = version

        if isinstance(fields, str):
            fields = (fields,)

        results = self.query(
            criteria=criteria, fields=fields, monty_decode=monty_decode, suburl=task_id
        )

        if not results:
            warnings.warn(f"No result for record {task_id}.")
            return
        elif len(results) > 1:
            raise ValueError(
                f"Multiple records for {task_id}, this shouldn't happen. Please report as a bug."
            )
        else:
            return results[0]

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
            return results["meta"]["total"]
        except Exception:
            return "unknown"

    @property
    def available_fields(self) -> List[str]:
        if self.document_model is None:
            return ["Unknown fields."]
        return list(self.document_model().fields.keys())  # type: ignore

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.endpoint}>"

    def __str__(self):
        if self.document_model is None:
            return self.__repr__()
        return (
            f"{self.__class__.__name__} connected to {self.endpoint}\n"
            f"Available fields: {', '.join(self.available_fields)}\n"
            f"Available documents: {self.count():n}"
        )


class MPRestError(Exception):
    """
    Raised when the query has problems, e.g., bad query format.
    """
