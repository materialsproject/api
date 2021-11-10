from pydantic import BaseSettings, Field
from mp_api import __file__ as root_dir
import os


class MAPISettings(BaseSettings):
    """
    Special class to store settings for MAPI
    python module
    """

    APP_PATH: str = Field(
        "~/mapi.json", description="Path for the default MAPI JSON definition"
    )

    DEBUG: bool = Field(False, description="Turns on debug mode for MAPI")

    TEST_FILES: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(root_dir)), "../../test_files"),
        description="Directory with test files",
    )

    DB_VERSION: str = Field("2021.11.10", description="Database version")

    DB_NAME_SUFFIX: str = Field(None, description="Database name suffix")

    REQUESTS_PER_MIN: int = Field(
        100, description="Number of requests per minute to for rate limit."
    )

    class Config:
        env_prefix = "MAPI_"
