from pydantic import BaseSettings, Field


class MAPISettings(BaseSettings):
    """
    Special class to store settings for MAPI
    python module
    """

    app_path: str = Field(
        "~/mapi.json", description="Path for the default MAPI JSON definition"
    )

    class Config:
        env_prefix = "MAPI"
