from typing import Dict, List
from maggma.api.resource.core import Resource
from pymatgen.core import __version__ as pmg_version  # type: ignore
from mp_api.core.settings import MAPISettings
from mp_api import __version__ as api_version
from fastapi.openapi.utils import get_openapi
from maggma.api.API import API


class MAPI(API):
    """
    Core Materials API that orchestrates resources together
    """

    def __init__(
        self,
        resources: Dict[str, List[Resource]],
        title="Materials Project API",
        version=api_version,
        debug=False,
        heartbeat_meta={
            "pymatgen": pmg_version,
            "db_version": MAPISettings().db_version,
        },
        description=None,
        tags_meta=None,
    ):
        super().__init__(
            resources=resources,
            title=title,
            version=version,
            debug=debug,
            heartbeat_meta=heartbeat_meta,
            description=description,
            tags_meta=tags_meta,
        )

    @property
    def app(self):
        """
        App server for the cluster manager
        """
        app = super().app

        def custom_openapi():
            openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                routes=app.routes,
                description=self.description,
                tags=self.tags_meta,
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
