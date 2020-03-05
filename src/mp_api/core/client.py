# coding: utf-8
"""
This module provides classes to interface with the Materials Project REST
API v3 to enable the creation of data structures and pymatgen objects using
Materials Project data.
"""

import json
import requests
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
                    "REST query returned with error status code {}".format(
                        response.status_code
                    )
                )

        except Exception as ex:
            msg = (
                "{}. Content: {}".format(str(ex), response.content)
                if hasattr(response, "content")
                else str(ex)
            )
            raise RESTError(msg)


class RESTError(Exception):
    """
    Raised when the query has problems, e.g., bad query format.
    """
