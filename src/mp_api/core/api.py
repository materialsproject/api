import os
import uvicorn
from starlette.responses import RedirectResponse
from fastapi import FastAPI
from typing import Dict, Union
from datetime import datetime
from monty.json import MSONable
from mp_api.core.resource import ConsumerPostResource, GetResource
from pymatgen.core import __version__ as pmg_version  # type: ignore
from fastapi.openapi.utils import get_openapi


class MAPI(MSONable):
    """
    Core Materials API that orchestrates resources together

    TODO:
        Build cross-resource relationships
        Global Query Operators?
    """

    def __init__(
        self,
        resources: Dict[str, Union[GetResource, ConsumerPostResource]],
        title="Materials Project API",
        version="3.0.0-dev",
        debug=False,
    ):
        self.resources = resources
        self.title = title
        self.version = version
        self.debug = debug

        if not debug:
            for resource in resources.values():
                resource.setup_indices()

    @property
    def app(self):
        """
        App server for the cluster manager
        """
        app = FastAPI(title=self.title, version=self.version)
        if len(self.resources) == 0:
            raise RuntimeError("ERROR: There are no resources provided")

        for prefix, endpoint in self.resources.items():
            app.include_router(endpoint.router, prefix=f"/{prefix}")

        @app.get("/heartbeat", include_in_schema=False)
        def heartbeat():
            """ API Heartbeat for Load Balancing """

            return {
                "status": "OK",
                "time": datetime.utcnow(),
                "api": self.version,
                "database": os.environ.get("DB_VERSION").replace("_", "."),
                "pymatgen": pmg_version,
            }

        @app.get("/", include_in_schema=False)
        def redirect_docs():
            """ Redirects the root end point to the docs """
            return RedirectResponse(url=app.docs_url, status_code=301)

        def custom_openapi():
            openapi_schema = get_openapi(
                title=self.title, version=self.version, routes=app.routes
            )

            openapi_schema["components"]["securitySchemes"] = {
                "ApiKeyAuth": {
                    "descriptions": "MP API key to authorize requests",
                    "name": "X-API-KEY",
                    "in": "header",
                    "type": "apiKey",
                }
            }

            openapi_schema["security"] = [{"ApiKeyAuth": []}]

            openapi_schema["info"]["x-logo"] = {
                "url": "https://raw.githubusercontent.com/materialsproject/api/master/src/mp_api/core/assets/mp_logo_small.png"  # noqa: E501
            }

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi

        return app

    def run(self, ip: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
        """
        Runs the Cluster Manager locally
        Meant for debugging purposes only

        Args:
            ip: Local IP to listen on
            port: Local port to listen on
            log_level: Logging level for the webserver

        Returns:
            None
        """

        uvicorn.run(self.app, host=ip, port=port, log_level=log_level, reload=False)
