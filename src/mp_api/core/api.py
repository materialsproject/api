import os
import uvicorn
from starlette.responses import RedirectResponse
from fastapi import FastAPI, Header
from typing import Dict
from datetime import datetime
from monty.json import MSONable
from mp_api.core.resource import Resource
from pymatgen import __version__ as pmg_version  # type: ignore
from fastapi.openapi.utils import get_openapi
import base64


class MAPI(MSONable):
    """
    Core Materials API that orchestrates resources together

    TODO:
        Build cross-resource relationships
        Global Query Operators?
    """

    def __init__(
        self,
        resources: Dict[str, Resource],
        title="Materials Project API",
        version="3.0.0-dev",
    ):
        self.resources = resources
        self.title = title
        self.version = version

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

        @app.get("/login", include_in_schema=False)
        def login(
            x_consumer_username: str = Header(None),
            x_consumer_custom_id: str = Header(None),
        ):

            return {
                "user": x_consumer_username,
                "api-key": base64.b64decode(x_consumer_custom_id).decode("utf-8"),
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
                "url": "https://github.com/materialsproject/web/blob/master/mp_web/assets/materials_project_logo.svg"
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
