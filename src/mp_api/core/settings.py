from pydantic import BaseSettings, Field
from mp_api import __file__ as root_dir
from typing import List
import os


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
        8, description="Number of parallel requests to send.",
    )

    MAX_RETRIES: int = Field(3, description="Maximum number of retries for requests.")

    MUTE_PROGRESS_BARS: bool = Field(
        False, description="Whether to mute progress bars when data is retrieved.",
    )

    class Config:
        env_prefix = "MPRESTER_"
