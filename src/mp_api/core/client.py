# coding: utf-8
"""
This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

import json
import requests
from requests.exceptions import RequestException
from typing import Dict, Optional
from monty.json import MontyDecoder
from pydantic import AnyUrl


class RESTer:
    """
    Base client class with core stubs
    """

    def __init__(self, endpoint, debug=True):
        """
        Arguments:
            endpoint: URL for the base endpoint to access
        """

        self.endpoint = endpoint
        self.debug = debug

        self.session = requests.Session()

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

    def _make_request(self, sub_url: AnyUrl, monty_decode: bool = True):
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
                raise RESTError(
                    f"REST query returned with error status code {response.status_code} on url {url} : {message}"
                )

        except RequestException as ex:

            raise RESTError(str(ex))

    def query(self, criteria: Optional[Dict] = None, monty_decode: bool = True):
        """
        Query the endpoint

        Arguments:
            critieria: dictionary of criteria to filter down
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
                data = json.loads(response.text, cls=MontyDecoder)["detail"]

                if data == "Not Found":
                    message = data + "  "
                else:
                    message = ""
                    try:
                        for entry in data:
                            message += "{} - {}, ".format(entry["loc"][1], entry["msg"])
                    except:
                        message += data

                raise RESTError(
                    f"REST query returned with error status code {response.status_code} on url {response.url} : {message[:-2]}"
                )

        except RequestException as ex:

            raise RESTError(str(ex))


class RESTError(Exception):
    """
    Raised when the query has problems, e.g., bad query format.
    """
