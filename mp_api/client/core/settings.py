import os
from multiprocessing import cpu_count
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymatgen.core import _load_pmg_settings

from mp_api.client import __file__ as root_dir

PMG_SETTINGS = _load_pmg_settings()
_MAX_RETRIES = min(PMG_SETTINGS.get("MPRESTER_MAX_RETRIES", 3), 3)
_MUTE_PROGRESS_BAR = PMG_SETTINGS.get("MPRESTER_MUTE_PROGRESS_BARS", False)
_MAX_LIST_LENGTH = min(PMG_SETTINGS.get("MPRESTER_MAX_LIST_LENGTH", 10000), 10000)

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

    MIN_EMMET_VERSION: str = Field(
        "0.54.0", description="Minimum compatible version of emmet-core for the client."
    )

    MAX_LIST_LENGTH: int = Field(
        _MAX_LIST_LENGTH, description="Maximum length of query parameter list"
    )

    model_config = SettingsConfigDict(env_prefix="MPRESTER_")
