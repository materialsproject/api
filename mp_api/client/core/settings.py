import os
from multiprocessing import cpu_count
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings
from pymatgen.core import _load_pmg_settings

from mp_api.client import __file__ as root_dir

PMG_SETTINGS = _load_pmg_settings()
_NUM_PARALLEL_REQUESTS = PMG_SETTINGS.get("MPRESTER_NUM_PARALLEL_REQUESTS", 8)
_MAX_RETRIES = PMG_SETTINGS.get("MPRESTER_MAX_RETRIES", 3)
_MUTE_PROGRESS_BAR = PMG_SETTINGS.get("MPRESTER_MUTE_PROGRESS_BARS", False)
_MAX_HTTP_URL_LENGTH = PMG_SETTINGS.get("MPRESTER_MAX_HTTP_URL_LENGTH", 2000)

try:
    CPU_COUNT = cpu_count()
except NotImplementedError:
    pass


class MAPIClientSettings(BaseSettings):
    """Special class to store settings for MAPI client
    python module.
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
        _NUM_PARALLEL_REQUESTS,
        description="Number of parallel requests to send.",
    )

    MAX_RETRIES: int = Field(
        _MAX_RETRIES, description="Maximum number of retries for requests."
    )

    BACKOFF_FACTOR: float = Field(
        0.1,
        description="A backoff factor to apply between retry attempts. To disable, set to 0.",
    )

    MUTE_PROGRESS_BARS: bool = Field(
        _MUTE_PROGRESS_BAR,
        description="Whether to mute progress bars when data is retrieved.",
    )

    MAX_HTTP_URL_LENGTH: int = Field(
        _MAX_HTTP_URL_LENGTH,
        description="Number of characters to use to define the maximum length of a given HTTP URL.",
    )

    MIN_EMMET_VERSION: str = Field(
        "0.54.0", description="Minimum compatible version of emmet-core for the client."
    )

    class Config:
        env_prefix = "MPRESTER_"
