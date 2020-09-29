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
from typing import Dict, Optional
from urllib.parse import urljoin

import requests
from monty.json import MontyDecoder
from pymatgen import __version__ as pmg_version
from requests.exceptions import RequestException


class BaseRester:
    """
    Base client class with core stubs
    """

    suffix = None

    def __init__(
        self,
        api_key=None,
        endpoint="https://api.materialsproject.org/",
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
        response = None
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
                message = json.loads(response.text, cls=MontyDecoder)["detail"]
                raise MPRestError(
                    f"REST query returned with error status code {response.status_code} on url {url} : {message}"
                )

        except RequestException as ex:

            raise MPRestError(str(ex))

    def query(self, criteria: Optional[Dict] = None, monty_decode: bool = True):
        """
        Query the endpoint

        Arguments:
            criteria: dictionary of criteria to filter down
            monty_decode: Decode the data using monty into python objects
        """

        criteria = (
            {k: v for k, v in criteria.items() if v is not None}
            if criteria is not None
            else None
        )

        response = None

        try:
            response = self.session.get(self.endpoint, verify=True, params=criteria)

            if response.status_code == 200:
                if monty_decode:
                    data = json.loads(response.text, cls=MontyDecoder)
                else:
                    data = json.loads(response.text)

                return data

            else:
                data = json.loads(response.text)["detail"]
                try:
                    data = json.loads(response.text)["detail"]
                except JSONDecodeError:
                    data = "Invalid data {}".format(response.text)
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


class MPRestError(Exception):
    """
    Raised when the query has problems, e.g., bad query format.
    """
