import os
from ratelimit import sleep_and_retry, limits
from mp_api.core.settings import MAPIClientSettings

DEFAULT_ENDPOINT = os.environ.get(
    "MP_API_ENDPOINT", "https://api.materialsproject.org/"
)


def check_limit():
    """
    Empty function for enabling global rate limiting.
    """
    return


if "api.materialsproject" in DEFAULT_ENDPOINT:
    check_limit = limits(calls=MAPIClientSettings().REQUESTS_PER_MIN, period=60)(
        check_limit
    )
    check_limit = sleep_and_retry(check_limit)
