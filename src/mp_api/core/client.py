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

                raise RESTError(
                    f"REST query returned with error status code {response.status_code} on url {url}"
                )

        except RequestException as ex:

            raise RESTError(str(ex))

    def _build_query_sub_url(self, criteria: Optional[Dict] = None):
        """
        Helper function to enable creating queries using a dictionary
        rather than building URL string

        Args:
            critieria: dictionary of criteria to filter down
        """
        query_params = [
            f"{arg}={value}" for arg, value in criteria.items() if value is not None
        ]
        query_string = "&".join(query_params)

        sub_url = f"?{query_string}" if len(query_string) > 0 else ""

        return sub_url

    def query(self, criteria: Optional[Dict] = None, monty_decode: bool = True):
        """
        Query the endpoint

        Arguments:
            critieria: dictionary of criteria to filter down
            monty_decode: Decode the data using monty into python objects
        """
        query_string = self._build_query_sub_url(criteria=criteria)
        response = self._make_request(query_string, monty_decode=monty_decode)
        return response


class RESTError(Exception):
    """
    Raised when the query has problems, e.g., bad query format.
    """
