from functools import cached_property
import os
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pymatgen.core import SETTINGS as _PMG_SETTINGS

from filetype.types import TYPES as _FILE_TYPES

_MEGABYTES: int = 2**20

_DEFAULT_SUBDOMAINS = ["contribs", "ml", "micro"]
_DEFAULT_PORTS = [5000, 5002, 5003, 5005, 10000, 10002, 10003, 10005, 20000, 20005]

_DEFAULT_HOSTS = [
    "localhost",
    "contribs-apis",
    *[f"192.168.0.{i}" for i in range(36, 47)],  # PrivateSubnetOne
    *[f"192.168.0.{i}" for i in range(52, 63)],  # PrivateSubnetTwo
]

_DEFAULT_URLS = {f"http://{h}:{p}" for p in _DEFAULT_PORTS for h in _DEFAULT_HOSTS}
_DEFAULT_URLS |= {
    f"https://{n}-api{m}.materialsproject.org"
    for n in _DEFAULT_SUBDOMAINS
    for m in ["", "-preview"]
}
_DEFAULT_URLS |= {
    f"http://localhost.{n}-api.materialsproject.org" for n in _DEFAULT_SUBDOMAINS
}


class ContribsClientSettings(BaseSettings):
    """Define core settings for MPContribs client."""

    RETRIES: int = 3
    MAX_WORKERS: int = 3
    MAX_ELEMS: int = 10
    MAX_NESTING: int = 5
    MAX_BYTES: float = 2.4 * _MEGABYTES
    MAX_PAYLOAD: float = 15 * _MEGABYTES
    MAX_COLUMNS: int = 160
    API_HOST: str = "contribs-api.materialsproject.org"
    BULMA: str = "is-narrow is-fullwidth has-background-light"
    PROVIDERS: set[str] = Field(
        default={"github", "google", "facebook", "microsoft", "amazon"}
    )
    COMPONENTS: list[str] = Field(
        ["structures", "tables", "attachments"],
        description="Ordered list of MPContribs components",
    )
    SUBDOMAINS: list[str] = Field(_DEFAULT_SUBDOMAINS)
    PORTS: list[int] = Field(_DEFAULT_PORTS)
    HOSTS: list[str] = Field(_DEFAULT_HOSTS)
    VALID_URLS: set[str] = Field(_DEFAULT_URLS)
    SUPPORTED_FILETYPES: set[str] = Field({"gz", "jpg", "png", "gif", "tif"})
    DEFAULT_DOWNLOAD_DIR: Path = Field(default=Path.home() / "mpcontribs-downloads")

    API_KEY: str | None = Field(None, description="The user's 32-character API key.")

    CLIENT_LOG_LEVEL: str = Field("INFO")

    model_config = SettingsConfigDict(env_prefix="MPCONTRIBS_")

    @cached_property
    def SUPPORTED_MIMES(self) -> set[str]:
        return {
            next(ftype for ftype in _FILE_TYPES if ftype.extension == ext).mime
            for ext in self.SUPPORTED_FILETYPES
        }

    @field_validator("API_KEY", mode="before")
    def get_api_key(cls, v) -> str | None:
        if not v:
            try:
                return next(
                    k
                    for k in (
                        os.environ.get("MP_API_KEY"),
                        _PMG_SETTINGS.get("PMG_MAPI_KEY"),
                    )
                    if k
                )
            except StopIteration:
                return None
        return v


MPCC_SETTINGS = ContribsClientSettings()  # type: ignore[call-arg]
