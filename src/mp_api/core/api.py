import uvicorn
from fastapi import FastAPI
from fastapi.routing import Request
from typing import Dict
from datetime import datetime
from monty.json import MSONable
from mp_api.core.resource import Resource


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
            return {"status": "OK", "time": datetime.utcnow()}

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
