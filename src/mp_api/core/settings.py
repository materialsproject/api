from pydantic import BaseSettings, Field


class MAPISettings(BaseSettings):
    """
    Special class to store settings for MAPI
    python module
    """

    app_path: str = Field(
        "~/mapi.json", description="Path for the default MAPI JSON definition"
    )

    debug: bool = Field(False, description="Turns on debug mode for MAPI")

    db_version: str = Field("2021_04_26", description="Database version")

    class Config:
        env_prefix = "mapi_"
