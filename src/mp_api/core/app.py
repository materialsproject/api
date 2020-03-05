"""
Special module to enable directly loading a MAPI Configuration file
and running for use in production-like environments
"""
from monty.serialization import loadfn
from pydantic import BaseSettings, Field


class MAPISettings(BaseSettings):
    """
    Special class to store settings for MAPI python module.
    This should be set using environment variables, not directly
    loaded 
    """

    app_path: str = Field(
        "~/mapi.json", description="Path for the default MAPI JSON definition"
    )

    class Config:

        env_prefix = "MAPI"


default_settings = MAPISettings()
mapi = loadfn(default_settings.app_path)
app = mapi.app
