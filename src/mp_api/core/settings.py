from pydantic import BaseSettings, Field
from mp_api import __file__ as root_dir
import os


class MAPISettings(BaseSettings):
    """
    Special class to store settings for MAPI
    python module
    """

    app_path: str = Field(
        "~/mapi.json", description="Path for the default MAPI JSON definition"
    )

    debug: bool = Field(False, description="Turns on debug mode for MAPI")

    test_files: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(root_dir)), "../../test_files"),
        description="Directory with test files",
    )

    db_version: str = Field("2021_prerelease", description="Database version")

    requests_per_min: int = Field(
        100, description="Number of requests per minute to for rate limit."
    )

    class Config:
        env_prefix = "mapi_"
