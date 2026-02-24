import os
from pathlib import Path

from emmet.core.settings import EmmetSettings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymatgen.core import _load_pmg_settings

from mp_api.client import __file__ as root_dir

PMG_SETTINGS = _load_pmg_settings()
_NUM_PARALLEL_REQUESTS = min(PMG_SETTINGS.get("MPRESTER_NUM_PARALLEL_REQUESTS", 4), 4)
_MAX_RETRIES = min(PMG_SETTINGS.get("MPRESTER_MAX_RETRIES", 3), 3)
_MUTE_PROGRESS_BAR = PMG_SETTINGS.get("MPRESTER_MUTE_PROGRESS_BARS", False)
_MAX_LIST_LENGTH = min(PMG_SETTINGS.get("MPRESTER_MAX_LIST_LENGTH", 10000), 10000)

_EMMET_SETTINGS = EmmetSettings()  # type: ignore[call-arg]
_DEFAULT_ENDPOINT = "https://api.materialsproject.org/"


class MAPIClientSettings(BaseSettings):
    """Special class to store settings for MAPI client
    python module.
    """

    TEST_FILES: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(root_dir)), "../../test_files"),
        description="Directory with test files",
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

    MIN_EMMET_VERSION: str = Field(
        "0.86.3rc0",
        description="Minimum compatible version of emmet-core for the client.",
    )

    MAX_LIST_LENGTH: int = Field(
        _MAX_LIST_LENGTH, description="Maximum length of query parameter list"
    )

    ENDPOINT: str = Field("", description="The default API endpoint to use.")

    LTOL: float = Field(
        _EMMET_SETTINGS.LTOL,
        description="Fractional length tolerance for structure matching",
    )

    STOL: float = Field(
        _EMMET_SETTINGS.STOL, description="Site tolerance for structure matching."
    )

    ANGLE_TOL: float = Field(
        _EMMET_SETTINGS.ANGLE_TOL,
        description="Angle tolerance for structure matching in degrees.",
    )

    LOCAL_DATASET_CACHE: Path = Field(
        Path("~/mp_datasets").expanduser(),
        description="Target directory for downloading full datasets",
    )

    DATASET_FLUSH_THRESHOLD: int = Field(
        int(2.75 * 1024**3),
        description="Threshold bytes to accumulate in memory before flushing dataset to disk",
    )

    model_config = SettingsConfigDict(env_prefix="MPRESTER_")

    @field_validator("ENDPOINT", mode="before")
    def _get_endpoint_from_env(cls, v: str | None) -> str:
        """Support setting endpoint via MP_API_ENDPOINT environment variable."""
        return v or os.environ.get("MP_API_ENDPOINT") or _DEFAULT_ENDPOINT


MAPI_CLIENT_SETTINGS: MAPIClientSettings = MAPIClientSettings()  # type: ignore[call-arg]
