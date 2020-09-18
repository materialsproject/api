from typing import List, Optional, Tuple

from mp_api.core.client import RESTer, RESTError


class DOSRESTer(RESTer):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the DOSRESTer with a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/dos/", **kwargs)

