from pydantic import BaseSettings, Field
from mp_api import __file__ as root_dir
import os


class MAPIClientSettings(BaseSettings):
    """
    Special class to store settings for MAPI client
    python module
    """

    REQUESTS_PER_MIN: int = Field(
        200, description="Number of requests per minute to for rate limit."
    )

