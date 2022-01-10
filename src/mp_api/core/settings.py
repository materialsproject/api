from pydantic import BaseSettings, Field
from mp_api import __file__ as root_dir
from typing import List
import os


class MAPIClientSettings(BaseSettings):
    """
    Special class to store settings for MAPI client
    python module
    """

    REQUESTS_PER_MIN: int = Field(
        200, description="Number of requests per minute to for rate limit."
    )

    TEST_FILES: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(root_dir)), "../../test_files"),
        description="Directory with test files",
    )

    QUERY_NO_PARALLEL: List[str] = Field(
        [
            "elements",
            "possible_species",
            "coordination_envs",
            "coordination_envs_anonymous",
            "has_props",
        ],
        description="List API query parameters that do not support parallel requests.",
    )

    NUM_PARALLEL_REQUESTS: int = Field(
        8, description="Number of parallel requests to send.",
    )

    MAX_RETRIES: int = Field(3, description="Maximum number of retries for requests.")
