from pydantic import BaseSettings, Field
from mp_api.client import __file__ as root_dir
from multiprocessing import cpu_count
from typing import List
import os

CPU_COUNT = 8

try:
    CPU_COUNT = cpu_count()
except NotImplementedError:
    pass


class MAPIClientSettings(BaseSettings):
    """
    Special class to store settings for MAPI client
    python module
    """

    TEST_FILES: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(root_dir)), "../../test_files"),
        description="Directory with test files",
    )

    QUERY_NO_PARALLEL: List[str] = Field(
        [
            "elements",
            "exclude_elements",
            "possible_species",
            "coordination_envs",
            "coordination_envs_anonymous",
            "has_props",
            "gb_plane",
            "rotation_axis",
            "keywords",
            "substrate_orientation",
            "film_orientation",
            "synthesis_type",
            "operations",
            "condition_mixing_device",
            "condition_mixing_media",
            "condition_heating_atmosphere",
            "operations",
            "_sort_fields",
            "_fields",
        ],
        description="List API query parameters that do not support parallel requests.",
    )

    NUM_PARALLEL_REQUESTS: int = Field(
        CPU_COUNT,
        description="Number of parallel requests to send.",
    )

    MAX_RETRIES: int = Field(3, description="Maximum number of retries for requests.")

    MUTE_PROGRESS_BARS: bool = Field(
        False,
        description="Whether to mute progress bars when data is retrieved.",
    )

    MAX_HTTP_URL_LENGTH: int = Field(
        2000,
        description="Number of characters to use to define the maximum length of a given HTTP URL.",
    )

    class Config:
        env_prefix = "MPRESTER_"
